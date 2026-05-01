from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

PAGE_WIDTH = 1240
PAGE_HEIGHT = 1754
MARGIN_X = 72
MARGIN_Y = 72
BOTTOM_MARGIN = 72
CONTENT_WIDTH = PAGE_WIDTH - (MARGIN_X * 2)

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "frontend-midterm-reviewer.pdf"


def load_font(size: int, bold: bool = False):
    font_candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf",
    ]
    for candidate in font_candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


FONT_TITLE = load_font(34, bold=True)
FONT_H2 = load_font(24, bold=True)
FONT_H3 = load_font(19, bold=True)
FONT_BODY = load_font(16, bold=False)
FONT_BODY_BOLD = load_font(16, bold=True)
FONT_SMALL = load_font(14, bold=False)
FONT_SMALL_BOLD = load_font(14, bold=True)


def line_height(font):
    return font.size + 8 if hasattr(font, "size") else 20


class PdfCanvas:
    def __init__(self):
        self.pages = []
        self.image = None
        self.draw = None
        self.y = MARGIN_Y
        self.new_page()

    def new_page(self):
        self.image = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), "white")
        self.draw = ImageDraw.Draw(self.image)
        self.pages.append(self.image)
        self.y = MARGIN_Y

    def ensure_space(self, height):
        if self.y + height > PAGE_HEIGHT - BOTTOM_MARGIN:
            self.new_page()

    def text_width(self, text, font):
        bbox = self.draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0]

    def wrap_text(self, text, font, width):
        normalized = str(text).replace("\r", "")
        paragraphs = normalized.split("\n")
        lines = []
        for paragraph in paragraphs:
            words = paragraph.split()
            if not words:
                lines.append("")
                continue
            current = words[0]
            for word in words[1:]:
                candidate = f"{current} {word}"
                if self.text_width(candidate, font) <= width:
                    current = candidate
                else:
                    lines.append(current)
                    current = word
            lines.append(current)
        return lines

    def draw_block(self, lines, font, x, width, fill="black", top_pad=0, bottom_pad=10):
        lh = line_height(font)
        height = (len(lines) * lh) + top_pad + bottom_pad
        self.ensure_space(height)
        y = self.y + top_pad
        for line in lines:
            self.draw.text((x, y), line, font=font, fill=fill)
            y += lh
        self.y += height

    def heading(self, text):
        lines = self.wrap_text(text, FONT_H2, CONTENT_WIDTH)
        self.draw_block(lines, FONT_H2, MARGIN_X, CONTENT_WIDTH, top_pad=8, bottom_pad=8)
        self.draw.line((MARGIN_X, self.y, PAGE_WIDTH - MARGIN_X, self.y), fill="#d8d8d8", width=1)
        self.y += 10

    def subheading(self, text):
        lines = self.wrap_text(text, FONT_H3, CONTENT_WIDTH)
        self.draw_block(lines, FONT_H3, MARGIN_X, CONTENT_WIDTH, top_pad=6, bottom_pad=4)

    def paragraph(self, text, small=False):
        font = FONT_SMALL if small else FONT_BODY
        lines = self.wrap_text(text, font, CONTENT_WIDTH)
        self.draw_block(lines, font, MARGIN_X, CONTENT_WIDTH, fill="#111111", top_pad=0, bottom_pad=8)

    def bullets(self, items):
        bullet_indent = 22
        for item in items:
            lines = self.wrap_text(item, FONT_BODY, CONTENT_WIDTH - bullet_indent)
            height = len(lines) * line_height(FONT_BODY) + 4
            self.ensure_space(height)
            self.draw.text((MARGIN_X, self.y), u"\u2022", font=FONT_BODY_BOLD, fill="#111111")
            y = self.y
            for line in lines:
                self.draw.text((MARGIN_X + bullet_indent, y), line, font=FONT_BODY, fill="#111111")
                y += line_height(FONT_BODY)
            self.y = y + 2
        self.y += 4

    def callout(self, text):
        lines = self.wrap_text(text, FONT_BODY, CONTENT_WIDTH - 28)
        height = len(lines) * line_height(FONT_BODY) + 24
        self.ensure_space(height)
        x0, y0 = MARGIN_X, self.y
        x1, y1 = PAGE_WIDTH - MARGIN_X, self.y + height
        self.draw.rectangle((x0, y0, x1, y1), fill="#f5f5f5", outline="#d8d8d8", width=1)
        self.draw.rectangle((x0, y0, x0 + 6, y1), fill="#111111")
        y = y0 + 12
        for line in lines:
            self.draw.text((x0 + 18, y), line, font=FONT_BODY, fill="#111111")
            y += line_height(FONT_BODY)
        self.y = y1 + 10

    def hero(self, title, subtitle, pills):
        box_height = 170
        self.ensure_space(box_height)
        x0, y0 = MARGIN_X, self.y
        x1, y1 = PAGE_WIDTH - MARGIN_X, self.y + box_height
        self.draw.rectangle((x0, y0, x1, y1), fill="#fafafa", outline="#d8d8d8", width=1)
        self.draw.text((x0 + 18, y0 + 16), title, font=FONT_TITLE, fill="#111111")
        sub_lines = self.wrap_text(subtitle, FONT_BODY, CONTENT_WIDTH - 36)
        y = y0 + 62
        for line in sub_lines:
            self.draw.text((x0 + 18, y), line, font=FONT_BODY, fill="#555555")
            y += line_height(FONT_BODY)
        pill_x = x0 + 18
        pill_y = y0 + 108
        for pill in pills:
            width = self.text_width(pill, FONT_SMALL_BOLD) + 18
            if pill_x + width > x1 - 18:
                pill_x = x0 + 18
                pill_y += 28
            self.draw.rectangle((pill_x, pill_y, pill_x + width, pill_y + 24), fill="#efefef", outline="#d8d8d8", width=1)
            self.draw.text((pill_x + 9, pill_y + 4), pill, font=FONT_SMALL_BOLD, fill="#111111")
            pill_x += width + 8
        self.y = y1 + 16

    def table(self, headers, rows, col_widths):
        padding = 8
        table_width = CONTENT_WIDTH
        widths = [int(table_width * width) for width in col_widths]
        widths[-1] = table_width - sum(widths[:-1])

        def wrapped_cells(cell_values, fonts):
            result = []
            for value, width, font in zip(cell_values, widths, fonts):
                result.append(self.wrap_text(value, font, width - (padding * 2)))
            return result

        def row_height(lines, font):
            return max(max(1, len(cell_lines)) * line_height(font) for cell_lines in lines) + (padding * 2)

        header_lines = wrapped_cells(headers, [FONT_SMALL_BOLD] * len(headers))
        header_height = row_height(header_lines, FONT_SMALL_BOLD)

        def draw_row(lines, fonts, bg_fill):
            nonlocal header_height
            height = max(
                max(1, len(cell_lines)) * line_height(font)
                for cell_lines, font in zip(lines, fonts)
            ) + (padding * 2)
            self.ensure_space(height)
            x = MARGIN_X
            y0 = self.y
            for idx, (cell_lines, width, font) in enumerate(zip(lines, widths, fonts)):
                self.draw.rectangle((x, y0, x + width, y0 + height), fill=bg_fill, outline="#d8d8d8", width=1)
                text_y = y0 + padding
                for line in cell_lines:
                    self.draw.text((x + padding, text_y), line, font=font, fill="#111111")
                    text_y += line_height(font)
                x += width
            self.y += height

        draw_row(header_lines, [FONT_SMALL_BOLD] * len(headers), "#f1f1f1")

        for row in rows:
            body_fonts = [FONT_SMALL] * len(row)
            row_lines = wrapped_cells(row, body_fonts)
            estimated_height = max(max(1, len(cell_lines)) * line_height(FONT_SMALL) for cell_lines in row_lines) + (padding * 2)
            if self.y + estimated_height > PAGE_HEIGHT - BOTTOM_MARGIN:
                self.new_page()
                draw_row(header_lines, [FONT_SMALL_BOLD] * len(headers), "#f1f1f1")
            draw_row(row_lines, body_fonts, "#ffffff")
        self.y += 10

    def save(self, path: Path):
        if not self.pages:
            raise RuntimeError("No pages to save")
        first, rest = self.pages[0], self.pages[1:]
        first.save(str(path), "PDF", resolution=150.0, save_all=True, append_images=rest)


def build_document():
    pdf = PdfCanvas()
    pdf.hero(
        "Aura Frontend Midterm Reviewer",
        "Interview guide for a student assigned to Frontend and Deployment responsibilities.",
        ["Vue 3", "Vite", "Vue Router", "API Integration", "Docker", "Deployment"],
    )

    pdf.heading("1. Role Summary")
    pdf.paragraph("You can introduce yourself like this:")
    pdf.callout(
        "I am responsible for frontend integration and deployment readiness. "
        "I worked on connecting the Vue frontend to the real backend, fixing broken user flows, "
        "organizing role-based navigation, and preparing the project so it can run in Docker and be demonstrated consistently."
    )
    pdf.table(
        ["Role Area", "What I Did", "Purpose", "Why It Matters"],
        [
            ["Attendance", "Integrated student sign-in, waiting-for-sign-out, sign-out, and final attendance state with backend rules.", "Make attendance accurate and match real event phases.", "Wrong state here affects attendance records, analytics, and email notifications."],
            ["SG/SSG Dashboard", "Separated SG workspace routing from normal student dashboard routing.", "Keep role-based views organized and prevent broken navbar behavior.", "Users need the correct dashboard and navigation context based on role."],
            ["Campus Admin", "Connected student import, event management, reports, and program student management to the backend.", "Allow real admin workflows instead of mock or broken actions.", "This is the main operational side used by school administrators."],
            ["Public Attendance", "Added Quick Attendance from the login side without requiring a user session.", "Support public face attendance for nearby events.", "Important for kiosk-like attendance use cases."],
            ["Deployment", "Prepared Docker, nginx proxying, runtime config, and environment-backed startup.", "Make the project easier for other teammates to run and demo.", "Deployment readiness is part of software ownership, not just coding."],
        ],
        [0.18, 0.33, 0.22, 0.27],
    )

    pdf.heading("2. Frontend Concepts You Must Explain")
    pdf.table(
        ["Term", "Meaning", "Frontend Example", "Purpose"],
        [
            ["API", "An interface the frontend uses to talk to the backend and exchange data.", "Frontend requests events, users, attendance records, and imports.", "Connect UI to real system data."],
            ["Endpoint", "A specific backend URL for one action or one resource.", "/api/events/, /api/attendance/me/records", "Defines exactly where a request goes."],
            ["Request Payload", "The data sent from frontend to backend.", "Creating an event with name, time, geofence, and scope data.", "Tells the backend what to create or update."],
            ["Response", "The data returned by the backend after a request.", "Attendance status, imported row summary, event list.", "Lets the UI update based on real backend state."],
            ["CORS", "Cross-Origin Resource Sharing. A browser security rule controlling whether a frontend can call a backend from another origin.", "Frontend on one host calling backend on another host.", "Without correct CORS or proxying, requests fail in the browser."],
            ["Proxy", "A middle layer that forwards frontend requests to the backend.", "The app uses /__backend__ and nginx or Vite proxying.", "Avoids CORS issues and keeps config flexible."],
        ],
        [0.16, 0.39, 0.23, 0.22],
    )

    pdf.heading("3. How Frontend Connects to the API")
    pdf.callout(
        "The frontend does not talk directly to the database. It sends HTTP requests to backend endpoints. "
        "In Aura, the frontend usually calls the backend through /__backend__ using runtime configuration, "
        "then service files normalize the responses so Vue components can display clean data."
    )
    pdf.table(
        ["Step", "What Happens", "Aura Example", "Why This Is Good Practice"],
        [
            ["1. UI action", "User clicks a button, submits a form, or opens a page.", "Student clicks Attendance Now.", "Business flow starts from a visible user event."],
            ["2. Service call", "A frontend service file sends the request.", "backendApi.js or publicAttendance.js", "Keeps API logic separate from UI."],
            ["3. Backend processing", "The backend validates, computes rules, and returns a result.", "Attendance phase decides sign-in, waiting, or sign-out.", "Important logic stays server-side, not hardcoded in UI."],
            ["4. Normalize result", "The frontend cleans response shape if needed.", "Attendance and import responses are normalized before use.", "Makes components simpler and more stable."],
            ["5. Update UI", "Vue state changes and the screen reacts.", "Button changes to Waiting for Sign Out.", "Gives users correct feedback immediately."],
        ],
        [0.14, 0.29, 0.27, 0.30],
    )

    pdf.heading("4. Important API and Frontend Terms")
    pdf.subheading("What is an Endpoint?")
    pdf.paragraph("An endpoint is a specific backend address used for one task.")
    pdf.bullets([
        "GET /api/events/ gets events",
        "PATCH /api/events/{id} updates an event",
        "DELETE /api/events/{id} deletes an event",
    ])
    pdf.subheading("What is CORS?")
    pdf.paragraph("CORS is a browser security rule. If the frontend and backend are on different origins, the backend must allow the frontend origin, or the browser blocks the request.")
    pdf.subheading("How Aura avoids CORS problems")
    pdf.bullets([
        "Vite development uses a proxy through /__backend__.",
        "Docker nginx also proxies /__backend__ to the backend host.",
        "This makes the browser see the requests as coming from the same frontend origin.",
    ])
    pdf.subheading("What happens without correct API integration?")
    pdf.bullets([
        "Buttons work visually but data is not saved.",
        "Wrong role gets the wrong screen.",
        "Attendance status becomes misleading.",
        "Import preview works but actual import fails.",
    ])

    pdf.heading("5. Project-Specific Work You Can Defend")
    pdf.table(
        ["Feature", "Your Contribution", "Backend/Frontend Connection", "Possible Interview Question"],
        [
            ["Attendance flow", "Fixed sign-in, waiting-for-sign-out, sign-out, and final dashboard count behavior.", "Frontend now follows backend attendance phases instead of guessing from event status.", "Why should attended only count after sign-out?"],
            ["SG/SSG navigation", "Fixed navbar and route context so SG workspace does not break student dashboard.", "Used role-aware routing and workspace context in Vue Router.", "What was causing the white screen or wrong dashboard?"],
            ["Student import", "Matched the preview-token import flow and improved success or error handling.", "Frontend previews file first, then imports using the backend preview token.", "Why not upload directly to import immediately?"],
            ["Event management", "Made edit and delete functional for campus admin and SG with a shared event editor UI.", "Uses real PATCH and DELETE event endpoints.", "What fields can actually be edited from the frontend?"],
            ["Public attendance", "Added Quick Attendance to login side without requiring a session.", "Connects to public attendance endpoints for nearby events and multi-face scanning.", "How can attendance happen without user login?"],
        ],
        [0.18, 0.28, 0.28, 0.26],
    )

    pdf.heading("6. Common Interview Questions with Suggested Answers")
    pdf.table(
        ["Question", "Suggested Answer"],
        [
            ["What is your role in the team?", "I am responsible for frontend integration and deployment readiness. I connect the UI to the backend, fix broken user flows, and make the app stable enough to run in browser and Docker demo environments."],
            ["What did you personally do?", "I worked on attendance integration, SG or SSG routing, campus admin event management, student import, Quick Attendance, and Docker-based deployment setup."],
            ["Why did you avoid hardcoding?", "Because attendance phases, role scope, import validation, and event rules belong to backend logic. Hardcoding would make the frontend fragile and inaccurate when backend data changes."],
            ["What will break if your work is removed?", "Attendance state would become inconsistent, SG workspace could route incorrectly, admin event actions may stop working, import could fail, and deployment would become harder to reproduce."],
            ["What was your biggest challenge?", "The hardest part was aligning the frontend to the real backend contracts. Many bugs were caused by small mismatches in endpoint path, payload shape, or expected response state."],
            ["What improvement would you suggest next?", "I would add automated end-to-end tests for attendance, import, and SG routing because these are multi-step flows with high regression risk."],
        ],
        [0.28, 0.72],
    )

    pdf.heading("7. Demo Checklist")
    pdf.bullets([
        "Show login and role-based access.",
        "Show student schedule and attendance button state changes.",
        "Show SG dashboard and event management flow.",
        "Show campus admin import preview and actual import.",
        "Show event reports and attendance records.",
        "Show Quick Attendance from login side.",
        "Explain Docker startup and backend proxying.",
    ])

    pdf.heading("8. Docker and Deployment Reviewer")
    pdf.table(
        ["File", "Purpose", "How to Explain It"],
        [
            ["docker-compose.yml", "Starts the frontend container with backend-related environment variables.", "This is the main deployment entry for local demo or team testing."],
            ["Dockerfile", "Builds the Vue app with Node, then serves it with nginx.", "This creates a production-like frontend container instead of running Vite dev mode."],
            ["nginx.conf.template", "Handles SPA routing and proxies /__backend__ to the backend host.", "This is how we support route refresh and avoid frontend or backend origin issues."],
            [".env.docker", "Stores backend origin and port values used by Docker.", "Teammates can change deployment target without editing source code."],
        ],
        [0.20, 0.36, 0.44],
    )
    pdf.paragraph("Command to start: docker compose --env-file .env.docker up --build -d")

    pdf.heading("9. Final 1-Minute Summary")
    pdf.callout(
        "My main contribution is frontend integration and deployment readiness. I connected the Vue frontend to the real backend, fixed role-based navigation, attendance logic, event management, import flows, and public attendance. I also helped make the project easier to run through Docker, nginx proxying, and environment-based configuration. My approach was to follow backend contracts instead of hardcoding frontend assumptions."
    )
    pdf.paragraph(
        "Prepared for Aura Midterm Interview Review. This document focuses on Frontend and Deployment responsibilities, using project-specific examples and simple explanations for live oral defense.",
        small=True,
    )

    pdf.save(OUTPUT)
    return OUTPUT


if __name__ == "__main__":
    output_path = build_document()
    print(output_path)
