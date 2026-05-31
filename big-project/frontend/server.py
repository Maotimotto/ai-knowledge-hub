"""
AI创作工坊 - Frontend HTTP Server

Simple threaded HTTP server to serve the frontend dashboard.
Proxies API requests to the backend.
"""

import os
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from typing import Optional


class FrontendHandler(SimpleHTTPRequestHandler):
    """HTTP handler that serves frontend files and proxies API calls."""

    directory = os.path.dirname(os.path.abspath(__file__))

    def do_GET(self) -> None:
        if self.path.startswith("/api/"):
            self._proxy_request("GET")
        elif self.path == "/" or self.path == "":
            self.path = "/index.html"
            super().do_GET()
        else:
            super().do_GET()

    def do_POST(self) -> None:
        if self.path.startswith("/api/"):
            self._proxy_request("POST")
        else:
            self.send_error(404, "Not found")

    def _proxy_request(self, method: str) -> None:
        """Proxy API requests to the backend service."""
        import httpx

        backend_url = os.environ.get("BACKEND_URL", "http://localhost:8000")
        url = f"{backend_url}{self.path}"

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length > 0 else None

            headers = {k: v for k, v in self.headers.items() if k.lower() not in ("host", "content-length")}

            with httpx.Client(timeout=30.0) as client:
                if method == "GET":
                    resp = client.get(url, headers=headers)
                else:
                    resp = client.post(url, content=body, headers=headers)

            self.send_response(resp.status_code)
            for key, value in resp.headers.items():
                if key.lower() not in ("transfer-encoding", "content-encoding"):
                    self.send_header(key, value)
            self.end_headers()
            self.wfile.write(resp.content)

        except Exception as e:
            self.send_error(502, f"Backend proxy error: {e}")

    def log_message(self, format: str, *args: object) -> None:
        """Override to use print instead of stderr."""
        print(f"[Frontend] {args[0]}")


def main(port: Optional[int] = None) -> None:
    """Start the frontend server."""
    port = port or int(os.environ.get("FRONTEND_PORT", "3000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), FrontendHandler)
    print(f"[Frontend] Serving on http://0.0.0.0:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[Frontend] Shutting down")
        server.shutdown()


if __name__ == "__main__":
    main()
