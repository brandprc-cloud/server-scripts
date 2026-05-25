#!/usr/bin/env python3
import http.server, subprocess, json, os

class HealthHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/health":
            self.send_response(404)
            self.end_headers()
            return
        try:
            r = subprocess.run(["systemctl", "is-active", "claude-telegram"],
                               capture_output=True, text=True, timeout=3)
            bot_status = r.stdout.strip()
        except Exception:
            bot_status = "unknown"
        ok = bot_status == "active"
        body = json.dumps({"status": "ok" if ok else "degraded", "bot": bot_status}).encode()
        self.send_response(200 if ok else 503)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, *args):
        pass

server = http.server.HTTPServer(("0.0.0.0", 8080), HealthHandler)
server.serve_forever()
