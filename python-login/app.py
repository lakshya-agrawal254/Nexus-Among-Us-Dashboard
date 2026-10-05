"""Among Us inspired local login demo. Requires Python 3.10+, no packages."""
import argparse
import getpass
import hashlib
import hmac
import json
import re
import secrets
import sqlite3
import threading
import time
from collections import defaultdict, deque
from contextlib import closing
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB = ROOT / "crew.sqlite3"
SESSIONS = {}
ATTEMPTS = defaultdict(deque)
LOCK = threading.Lock()
SESSION_SECONDS = 1800


def normalize(registration, phone):
    if not isinstance(registration, str) or not isinstance(phone, str):
        raise ValueError("Enter your registration number and phone number.")
    registration = registration.strip().upper()
    if not re.fullmatch(r"[A-Z0-9][A-Z0-9-]{2,29}", registration):
        raise ValueError("Use 3–30 letters, numbers or hyphens for your registration number.")
    if not re.fullmatch(r"\+?[0-9 ()-]{10,25}", phone.strip()):
        raise ValueError("Enter a valid phone number using 10–15 digits.")
    phone = re.sub(r"[^0-9]", "", phone)
    if not 10 <= len(phone) <= 15:
        raise ValueError("Enter a valid phone number using 10–15 digits.")
    return registration, phone


def phone_hash(phone, salt):
    return hashlib.pbkdf2_hmac("sha256", phone.encode(), bytes.fromhex(salt), 250_000).hex()


def add_user(registration, phone, name):
    registration, phone = normalize(registration, phone)
    name = name.strip()
    if not 1 <= len(name) <= 80:
        raise ValueError("Name must contain 1–80 characters.")
    salt = secrets.token_hex(16)
    with closing(sqlite3.connect(DB)) as db, db:
        db.execute("INSERT INTO crew VALUES (?, ?, ?, ?)",
                   (registration, name, salt, phone_hash(phone, salt)))


def init_db():
    first_run = not DB.exists()
    with closing(sqlite3.connect(DB)) as db, db:
        db.execute("CREATE TABLE IF NOT EXISTS crew (registration TEXT PRIMARY KEY, name TEXT NOT NULL, salt TEXT NOT NULL, phone_hash TEXT NOT NULL)")
    if first_run:
        add_user("CREW001", "9876543210", "Red")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass  # Never log submitted credentials.

    def send(self, status, body, content_type="application/json", cookie=None):
        if isinstance(body, dict):
            body = json.dumps(body).encode()
        elif isinstance(body, str):
            body = body.encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        self.wfile.write(body)

    def session_token(self):
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get("Cookie", ""))
            return cookie["crew_session"].value if "crew_session" in cookie else ""
        except Exception:
            return ""

    def do_GET(self):
        if self.path == "/api/me":
            token = self.session_token()
            with LOCK:
                record = SESSIONS.get(token)
                if record and record["expires"] <= time.time():
                    SESSIONS.pop(token, None)
                    record = None
            if not record:
                return self.send(401, {"error": "Please sign in to join the crew."})
            return self.send(200, {"name": record["name"], "registration": record["registration"]})
        files = {"/": ("index.html", "text/html; charset=utf-8"),
                 "/style.css": ("style.css", "text/css; charset=utf-8"),
                 "/mobile.css": ("mobile.css", "text/css; charset=utf-8"),
                 "/app.js": ("app.js", "text/javascript; charset=utf-8"),
                 "/favicon.svg": ("favicon.svg", "image/svg+xml")}
        if self.path not in files:
            return self.send(404, {"error": "Not found"})
        filename, content_type = files[self.path]
        self.send(200, (ROOT / "static" / filename).read_bytes(), content_type)

    def do_POST(self):
        # JSON plus an exact same-origin check blocks cross-site form submissions.
        expected_origin = f"http://{self.headers.get('Host', '')}"
        if self.headers.get("Origin") != expected_origin:
            return self.send(403, {"error": "Please submit the form from this page."})
        if self.path == "/api/logout":
            with LOCK:
                SESSIONS.pop(self.session_token(), None)
            return self.send(200, {"ok": True}, cookie="crew_session=; Path=/; HttpOnly; SameSite=Strict; Max-Age=0")
        if self.path != "/api/login":
            return self.send(404, {"error": "Not found"})
        if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
            return self.send(415, {"error": "Expected JSON."})
        with LOCK:
            now = time.time()
            for key in list(SESSIONS):
                if SESSIONS[key]["expires"] <= now:
                    del SESSIONS[key]
            attempts = ATTEMPTS[self.client_address[0]]
            while attempts and now - attempts[0] >= 60:
                attempts.popleft()
            if len(attempts) >= 8:
                return self.send(429, {"error": "Too many attempts. Wait a minute and try again."})
            attempts.append(now)
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 2048:
                raise ValueError("Please check your details and try again.")
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ValueError("Please check your details and try again.")
            registration, phone = normalize(data.get("registration"), data.get("phone"))
        except (ValueError, UnicodeDecodeError):
            return self.send(400, {"error": "Enter a registration number (3–30 letters, numbers or hyphens) and a phone number (10–15 digits)."})
        with closing(sqlite3.connect(DB)) as db, db:
            row = db.execute("SELECT name, salt, phone_hash FROM crew WHERE registration = ?", (registration,)).fetchone()
        candidate = phone_hash(phone, row[1] if row else "00" * 16)
        if not row or not hmac.compare_digest(candidate, row[2]):
            return self.send(401, {"error": "Those details don’t match our crew records. Check both numbers and try again."})
        token = secrets.token_urlsafe(32)
        with LOCK:
            SESSIONS.pop(self.session_token(), None)
            SESSIONS[token] = {"name": row[0], "registration": registration, "expires": time.time() + SESSION_SECONDS}
        self.send(200, {"name": row[0], "registration": registration},
                  cookie=f"crew_session={token}; Path=/; HttpOnly; SameSite=Strict; Max-Age={SESSION_SECONDS}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", default="127.0.0.1", help="Bind address; use 0.0.0.0 to test from a phone on your Wi-Fi")
    parser.add_argument("--add-user", metavar="REGISTRATION")
    parser.add_argument("--name", default="Crewmate")
    args = parser.parse_args()
    init_db()
    if args.add_user:
        try:
            add_user(args.add_user, getpass.getpass("Phone number (hidden): "), args.name)
            print("Crew record added.")
        except (ValueError, sqlite3.IntegrityError) as exc:
            parser.error(str(exc))
    else:
        print(f"Crew login is ready at http://{args.host}:{args.port}", flush=True)
        if args.host == "0.0.0.0":
            print(f"On your phone, open http://<your-computer-LAN-IP>:{args.port} on the same Wi-Fi.", flush=True)
        print("Demo: CREW001 / 9876543210. Press Ctrl+C to stop.", flush=True)
        try:
            ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()
        except KeyboardInterrupt:
            print("\nShip offline.")
