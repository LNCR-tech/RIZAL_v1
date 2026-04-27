from __future__ import annotations

import html
import json
import socket
import struct
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Generator
from urllib.parse import parse_qs, quote, urlparse


DOCKER_SOCKET = "/var/run/docker.sock"
DOCKER_API_VERSION = "v1.43"
HOST = "0.0.0.0"
PORT = 8080


INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Rizal Local Logs</title>
  <style>
    :root {
      color-scheme: dark;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #101418;
      color: #e8edf2;
    }
    * { box-sizing: border-box; }
    body { margin: 0; min-height: 100vh; background: #101418; }
    header {
      display: grid;
      gap: 12px;
      grid-template-columns: minmax(180px, 1fr) auto auto;
      align-items: end;
      padding: 16px;
      border-bottom: 1px solid #25313b;
      background: #151b21;
    }
    label { display: grid; gap: 6px; color: #9fb0bf; font-size: 12px; }
    select, input, button {
      min-height: 38px;
      border: 1px solid #344552;
      border-radius: 6px;
      background: #0f1419;
      color: #e8edf2;
      padding: 8px 10px;
      font: inherit;
    }
    button { cursor: pointer; background: #203445; }
    button:hover { background: #2a4357; }
    main { height: calc(100vh - 72px); display: grid; grid-template-rows: auto 1fr; }
    .status { padding: 8px 16px; color: #9fb0bf; border-bottom: 1px solid #25313b; }
    pre {
      margin: 0;
      padding: 16px;
      overflow: auto;
      white-space: pre-wrap;
      word-break: break-word;
      font: 13px/1.45 Consolas, "SFMono-Regular", Menlo, monospace;
      background: #0b0f13;
      color: #dce6ee;
    }
    @media (max-width: 760px) {
      header { grid-template-columns: 1fr; align-items: stretch; }
      main { height: auto; min-height: calc(100vh - 190px); }
      pre { min-height: calc(100vh - 230px); }
    }
  </style>
</head>
<body>
  <header>
    <label>
      Container
      <select id="container"></select>
    </label>
    <label>
      Filter
      <input id="filter" placeholder="backend, worker, postgres">
    </label>
    <button id="clear" type="button">Clear</button>
  </header>
  <main>
    <div id="status" class="status">Loading containers...</div>
    <pre id="logs"></pre>
  </main>
  <script>
    const containerSelect = document.getElementById("container");
    const filterInput = document.getElementById("filter");
    const clearButton = document.getElementById("clear");
    const statusEl = document.getElementById("status");
    const logsEl = document.getElementById("logs");
    let containers = [];
    let stream = null;

    function labelFor(item) {
      const name = (item.Names && item.Names[0] || item.Id || "").replace(/^\//, "");
      return `${name}  |  ${item.Image}  |  ${item.Status}`;
    }

    function renderContainers() {
      const filter = filterInput.value.trim().toLowerCase();
      const visible = containers.filter((item) => labelFor(item).toLowerCase().includes(filter));
      containerSelect.innerHTML = "";
      for (const item of visible) {
        const option = document.createElement("option");
        option.value = item.Id;
        option.textContent = labelFor(item);
        containerSelect.appendChild(option);
      }
      if (visible.length) {
        startStream(visible[0].Id);
      } else {
        stopStream();
        statusEl.textContent = "No matching containers.";
      }
    }

    function stopStream() {
      if (stream) {
        stream.close();
        stream = null;
      }
    }

    function startStream(id) {
      stopStream();
      logsEl.textContent = "";
      const selected = containers.find((item) => item.Id === id);
      statusEl.textContent = selected ? `Following ${labelFor(selected)}` : "Following logs...";
      stream = new EventSource(`/api/stream?container=${encodeURIComponent(id)}&tail=250`);
      stream.onmessage = (event) => {
        logsEl.textContent += JSON.parse(event.data);
        logsEl.scrollTop = logsEl.scrollHeight;
      };
      stream.onerror = () => {
        statusEl.textContent = "Log stream disconnected. Select a container or refresh the page to reconnect.";
      };
    }

    async function loadContainers() {
      const response = await fetch("/api/containers");
      containers = await response.json();
      renderContainers();
    }

    containerSelect.addEventListener("change", () => startStream(containerSelect.value));
    filterInput.addEventListener("input", renderContainers);
    clearButton.addEventListener("click", () => { logsEl.textContent = ""; });
    loadContainers().catch((error) => {
      statusEl.textContent = `Unable to load containers: ${error}`;
    });
  </script>
</body>
</html>
"""


def docker_get(path: str, *, stream: bool = False):
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect(DOCKER_SOCKET)
    request = (
        f"GET /{DOCKER_API_VERSION}{path} HTTP/1.1\r\n"
        "Host: docker\r\n"
        "Connection: close\r\n"
        "\r\n"
    )
    sock.sendall(request.encode("ascii"))
    fileobj = sock.makefile("rb")
    status = fileobj.readline().decode("iso-8859-1", errors="replace").strip()
    headers: dict[str, str] = {}
    while True:
        line = fileobj.readline()
        if line in (b"\r\n", b"\n", b""):
            break
        key, _, value = line.decode("iso-8859-1", errors="replace").partition(":")
        headers[key.lower()] = value.strip().lower()
    if " 200 " not in status and not status.endswith(" 200 OK"):
        body = b"".join(iter_http_body(fileobj, headers))
        sock.close()
        raise RuntimeError(f"Docker API request failed: {status} {body.decode(errors='replace')}")
    if stream:
        return sock, iter_http_body(fileobj, headers)
    body = b"".join(iter_http_body(fileobj, headers))
    sock.close()
    return body


def iter_http_body(fileobj, headers: dict[str, str]) -> Generator[bytes, None, None]:
    if headers.get("transfer-encoding") == "chunked":
        while True:
            size_line = fileobj.readline()
            if not size_line:
                return
            size_text = size_line.split(b";", 1)[0].strip()
            if not size_text:
                continue
            size = int(size_text, 16)
            if size == 0:
                return
            chunk = fileobj.read(size)
            fileobj.read(2)
            if chunk:
                yield chunk
    else:
        while True:
            chunk = fileobj.read(8192)
            if not chunk:
                return
            yield chunk


class DockerLogDecoder:
    def __init__(self) -> None:
        self.buffer = b""
        self.raw = False

    def feed(self, chunk: bytes) -> str:
        if self.raw:
            return chunk.decode("utf-8", errors="replace")
        self.buffer += chunk
        output: list[str] = []
        while self.buffer:
            if len(self.buffer) < 8:
                return "".join(output)
            stream_type = self.buffer[0]
            padding = self.buffer[1:4]
            size = struct.unpack(">I", self.buffer[4:8])[0]
            if stream_type not in (1, 2) or padding != b"\x00\x00\x00":
                self.raw = True
                output.append(self.buffer.decode("utf-8", errors="replace"))
                self.buffer = b""
                return "".join(output)
            if len(self.buffer) < 8 + size:
                return "".join(output)
            payload = self.buffer[8 : 8 + size]
            self.buffer = self.buffer[8 + size :]
            output.append(payload.decode("utf-8", errors="replace"))
        return "".join(output)


class Handler(BaseHTTPRequestHandler):
    server_version = "RizalLogViewer/1.0"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.respond(200, INDEX_HTML.encode("utf-8"), "text/html; charset=utf-8")
            return
        if parsed.path == "/api/containers":
            self.handle_containers()
            return
        if parsed.path == "/api/stream":
            self.handle_stream(parsed.query)
            return
        self.respond(404, b"Not found", "text/plain; charset=utf-8")

    def handle_containers(self) -> None:
        body = docker_get("/containers/json?all=1")
        self.respond(200, body, "application/json; charset=utf-8")

    def handle_stream(self, query: str) -> None:
        params = parse_qs(query)
        container = params.get("container", [""])[0]
        tail = params.get("tail", ["250"])[0]
        if not container:
            self.respond(400, b"Missing container", "text/plain; charset=utf-8")
            return
        path = (
            f"/containers/{quote(container, safe='')}/logs"
            f"?stdout=1&stderr=1&timestamps=1&follow=1&tail={quote(tail, safe='')}"
        )
        sock = None
        try:
            sock, chunks = docker_get(path, stream=True)
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            decoder = DockerLogDecoder()
            for chunk in chunks:
                text = decoder.feed(chunk)
                if not text:
                    continue
                event = f"data: {json.dumps(text)}\n\n".encode("utf-8")
                self.wfile.write(event)
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            return
        except Exception as exc:
            message = html.escape(str(exc)).encode("utf-8")
            self.respond(500, message, "text/plain; charset=utf-8")
        finally:
            if sock is not None:
                sock.close()

    def respond(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args) -> None:
        print(f"{self.address_string()} - {fmt % args}", flush=True)


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Rizal local log viewer listening on http://{HOST}:{PORT}", flush=True)
    server.serve_forever()
