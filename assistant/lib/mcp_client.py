import asyncio
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MultiMCPClient:
    def __init__(self):
        self.sessions: Dict[str, ClientSession] = {}
        self.server_params: Dict[str, StdioServerParameters] = {}
        self.tool_map: Dict[str, str] = {} # tool_name -> server_name
        self._tools_cache: Optional[List[Dict[str, Any]]] = None
        self._tools_cache_at: float = 0.0
        self._tools_lock = asyncio.Lock()
        self._load_config()

    def _load_config(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        config_path = os.path.join(base_dir, "mcp_config.json")
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                for name, server in config.get("mcpServers", {}).items():
                    env = os.environ.copy()
                    if "env" in server:
                        env.update(server["env"])
                    
                    # Ensure the current venv's python is used instead of system "python"
                    command = sys.executable if server.get("command") == "python" else server.get("command")
                    
                    # Resolve relative paths in args to absolute paths based on assistant base dir
                    args = []
                    for arg in server.get("args", []):
                        if arg.startswith("mcp_servers/"):
                            arg = os.path.join(base_dir, arg)
                        args.append(arg)
                    
                    self.server_params[name] = StdioServerParameters(
                        command=command,
                        args=args,
                        env=env
                    )
            print(f"Loaded {len(self.server_params)} MCP servers from config.")
        except Exception as e:
            print(f"Failed to load mcp_config.json: {e}")

    async def get_all_tools(self, *, force_refresh: bool = False, ttl_seconds: int = 300) -> List[Dict[str, Any]]:
        """
        Connects to all servers and discovers their tools, building a tool_map.

        Cached by default to avoid re-listing tools on every user message.
        """
        now = time.time()
        if not force_refresh and self._tools_cache is not None and (now - self._tools_cache_at) < ttl_seconds:
            return list(self._tools_cache)

        async with self._tools_lock:
            now = time.time()
            if not force_refresh and self._tools_cache is not None and (now - self._tools_cache_at) < ttl_seconds:
                return list(self._tools_cache)

            all_tools: List[Dict[str, Any]] = []
            tool_map: Dict[str, str] = {}
            for name, params in self.server_params.items():
                try:
                    async with stdio_client(params) as (read, write):
                        async with ClientSession(read, write) as session:
                            await session.initialize()
                            tools_result = await session.list_tools()
                            for tool in tools_result.tools:
                                tool_dict = tool.model_dump()
                                tool_map[tool.name] = name
                                all_tools.append(tool_dict)
                except Exception as e:
                    print(f"Failed to load tools from {name}: {e}")

            # Update cache and routing map atomically.
            self.tool_map = tool_map
            self._tools_cache = all_tools
            self._tools_cache_at = time.time()
            return list(all_tools)

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Calls a specific tool using the internal tool_map for routing.
        """
        server_name = self.tool_map.get(tool_name)
        if not server_name:
            raise ValueError(f"Unknown tool: {tool_name}. Was it registered?")
        
        params = self.server_params[server_name]
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)
                return result.content[0].text if result.content else "{}"
