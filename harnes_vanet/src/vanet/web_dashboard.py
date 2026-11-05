"""Live dashboard in the web browser (no Qt/Tk needed).

A tiny HTTP server from the Python standard library runs in a background thread:
  /       -> dashboard.html (two cluster maps + four live graphs, drawn with <canvas>)
  /state  -> latest state as JSON (the page polls it every 0.5 s)
"""
import json
import os
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard.html")


class WebDashboard:
    def __init__(self, port=8765, open_browser=True):
        self._lock = threading.Lock()
        self._state = b"{}"
        self.static = {}
        page = open(HTML, "rb").read()
        dash = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path.startswith("/state"):
                    with dash._lock:
                        body, ctype = dash._state, "application/json"
                elif self.path in ("/", "/index.html"):
                    body, ctype = page, "text/html; charset=utf-8"
                else:
                    self.send_error(404)
                    return
                self.send_response(200)
                self.send_header("Content-Type", ctype)
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *a):      # keep the terminal clean
                pass

        self.server = None
        for p in range(port, port + 20):
            try:
                self.server = ThreadingHTTPServer(("127.0.0.1", p), Handler)
                break
            except OSError:
                continue
        if self.server is None:
            raise RuntimeError("no free port for the dashboard")
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}/"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        print(f"DASHBOARD: open {self.url} in your browser", flush=True)
        if open_browser:
            try:
                webbrowser.open(self.url)
            except Exception:
                pass

    def publish(self, state):
        state = dict(self.static, **state)
        data = json.dumps(state, separators=(",", ":")).encode()
        with self._lock:
            self._state = data

    def close(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
