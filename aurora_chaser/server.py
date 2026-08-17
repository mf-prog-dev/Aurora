from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .app import build_assessments, render_dashboard


class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path not in ("/", "/index.html"):
            self.send_error(404)
            return
        assessments, statuses = build_assessments()
        html = render_dashboard(assessments, statuses).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(html)))
        self.end_headers()
        self.wfile.write(html)

    def log_message(self, format: str, *args) -> None:
        return


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8765), DashboardHandler)
    print("Fairbanks Aurora Chaser running at http://127.0.0.1:8765")
    server.serve_forever()


if __name__ == "__main__":
    main()

