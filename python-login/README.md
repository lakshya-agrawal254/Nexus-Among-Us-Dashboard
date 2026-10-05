# Crew Check — Among Us inspired Python login

A responsive login page with animated CSS crewmates, server-side registration/phone matching, a SQLite database, and a signed-in welcome screen. No external packages, fonts, or images are needed. Requires Python 3.10 or later.

## Run

Open a terminal in this folder and run:

```sh
python app.py
```

Open http://127.0.0.1:8000. Use `python app.py --port 8001` to choose another port.

Click **Use demo**, then **Let me in**, or enter:

- Registration number: `CREW001`
- Phone number: `9876543210`

On first launch, the app creates `crew.sqlite3` and this sample record. The phone number is a demo value, not a contact number.

## Open on a phone

The layout adapts to narrow phone screens, with 16px inputs, 48px or larger tap targets, a telephone keypad, and safe-area spacing. The compact header keeps the login form close to the top. The page remains scrollable when the keyboard is open and supports reduced-motion preferences.

Run Python on your computer, and connect your phone to the same trusted Wi-Fi:

```sh
python app.py --host 0.0.0.0
```

Find your computer's Wi-Fi IPv4 address (`ipconfig` on Windows), then open `http://YOUR-COMPUTER-IP:8000` in your phone's browser. `localhost` on the phone refers to the phone itself. If prompted by your firewall, allow the server only on your private network. This optional mode exposes the demo to devices on that network; use sample data over HTTP and do not forward the port to the internet. Without `--host`, access stays on your computer.

## Add a record

```sh
python app.py --add-user REG2026001 --name "Your Name"
```

Enter the phone number at the hidden prompt. Registration numbers are case insensitive and must contain 3–30 letters, digits, or hyphens. Phone numbers accept 10–15 digits with optional spaces, parentheses, hyphens, and a leading plus. Include the same country code when adding and signing in; country codes are not inferred. Duplicate registration numbers are rejected.

## Files

Run the integration checks from this folder with `python test_login.py`. They use a temporary database and an ephemeral local server, covering valid and invalid credentials, custom records, session expiry, sign-out, rate limiting, static assets, and blocked file access.

- `app.py`: Python HTTP server, SQLite records, validation, session handling, and record creation command.
- `static/index.html`: Login and welcome views.
- `static/style.css`: Responsive theme and CSS crewmates.
- `static/mobile.css`: Phone layout, safe-area spacing, readable fields, and touch targets.
- `static/app.js`: Form submission, demo autofill, and sign-out.

The server matches both fields against one stored record using a parameterized SQL lookup and a salted PBKDF2 phone hash. Invalid combinations receive a generic error. Sessions expire after 30 minutes and are cleared when the server restarts. Cookies are HttpOnly and SameSite=Strict. Sign-in attempts are limited to 8 per minute per client address. The database is never served as a static file.

This is a local learning/demo project. Matching a known phone number does not prove ownership of that number. For real accounts, use verified OTP or another authentication factor, HTTPS with Secure cookies, and a production server/session store. The server defaults to listening only on your own computer; LAN testing is opt-in. The demo record is public and must not be used for real access control.

Fan-made artwork inspired by Among Us; not affiliated with Innersloth.
