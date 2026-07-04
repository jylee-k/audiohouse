import json
import sys
import os
from http.server import BaseHTTPRequestHandler

# Make root-level solver.py importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from solver import optimize_invoices


class handler(BaseHTTPRequestHandler):
    """Vercel Python serverless handler for POST /api/optimize."""

    def _send_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors()
        self.end_headers()

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            result = optimize_invoices(
                body["items"],
                additional_cashback=body.get("additional_cashback", 0),
            )
            payload = json.dumps(result).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(payload)
        except Exception as exc:
            error = json.dumps({"error": str(exc)}).encode()
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(error)

    def log_message(self, fmt, *args):
        pass
