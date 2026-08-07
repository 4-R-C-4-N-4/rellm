#!/usr/bin/env python3
"""Phone-friendly adjudication server for the homology gold set.

Serves tools/adjudicate_gold.html with data/homology/gold/candidates.jsonl
injected, and persists every verdict tap to data/homology/gold/verdicts.json.
Binds 0.0.0.0 so it is reachable over tailscale.

    python3 tools/adjudicate_gold.py [--port 8377]

verdicts.json shape: {"<candidate id>": {"verdict": ..., "note": ..., "synced": bool}}
Ratification into ratified.jsonl happens afterwards from this file.
"""
import argparse
import json
import os
import subprocess
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "data" / "homology" / "gold"
CANDIDATES = GOLD / "candidates.jsonl"
VERDICTS = GOLD / "verdicts.json"
APP = Path(__file__).with_suffix(".html")

_lock = threading.Lock()


def load_verdicts() -> dict:
    if VERDICTS.exists():
        return json.loads(VERDICTS.read_text())
    return {}


def save_verdicts(v: dict) -> None:
    fd, tmp = tempfile.mkstemp(dir=GOLD, prefix=".verdicts-", suffix=".json")
    with os.fdopen(fd, "w") as f:
        json.dump(v, f, ensure_ascii=False, indent=1)
    os.replace(tmp, VERDICTS)


def build_page() -> bytes:
    records = [
        json.loads(line)
        for line in CANDIDATES.read_text().splitlines()
        if line.strip()
    ]
    data = json.dumps(records, ensure_ascii=False).replace("</", "<\\/")
    html = APP.read_text().replace("/*__DATA__*/[]", data, 1)
    return html.encode()


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, ctype: str) -> None:
        try:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass  # phone dropped the connection (screen lock, roaming); state is already safe

    def handle(self):
        try:
            super().handle()
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, build_page(), "text/html; charset=utf-8")
        elif self.path == "/api/state":
            with _lock:
                body = json.dumps({"verdicts": load_verdicts()}).encode()
            self._send(200, body, "application/json")
        else:
            self._send(404, b"not found", "text/plain")

    def do_POST(self):
        if self.path != "/api/verdict":
            self._send(404, b"not found", "text/plain")
            return
        length = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(length))
            cid = payload.pop("id")
        except (json.JSONDecodeError, KeyError):
            self._send(400, b"bad payload", "text/plain")
            return
        entry = {
            k: payload[k]
            for k in ("verdict", "note", "synced")
            if k in payload and payload[k] not in (None, "")
        }
        with _lock:
            verdicts = load_verdicts()
            if entry:
                verdicts[cid] = entry
            else:
                verdicts.pop(cid, None)
            save_verdicts(verdicts)
        self._send(200, b"{\"ok\": true}", "application/json")

    def log_message(self, fmt, *args):  # keep the terminal quiet
        pass


def tailscale_ip() -> str | None:
    try:
        out = subprocess.run(
            ["tailscale", "ip", "-4"], capture_output=True, text=True, timeout=5
        )
        ip = out.stdout.strip().splitlines()
        return ip[0] if ip else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8377)
    args = ap.parse_args()

    if not CANDIDATES.exists():
        raise SystemExit(f"missing {CANDIDATES}")

    server = ThreadingHTTPServer(("0.0.0.0", args.port), Handler)
    ts = tailscale_ip()
    print(f"serving gold-set adjudicator on port {args.port}")
    if ts:
        print(f"  phone (tailscale): http://{ts}:{args.port}/")
    print(f"  local:             http://127.0.0.1:{args.port}/")
    print(f"verdicts -> {VERDICTS}")
    server.serve_forever()


if __name__ == "__main__":
    main()
