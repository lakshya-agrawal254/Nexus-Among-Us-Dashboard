# Python login

Among Us inspired login using a registration number and phone number. Requires Python 3.10+; no packages to install.

## Run

From this folder:

```sh
python app.py
```

Open http://127.0.0.1:8000. Demo: `CREW001` / `9876543210`.

## Open on your phone

```sh
python app.py --host 0.0.0.0
```

Connect your phone to the same trusted Wi-Fi and open `http://YOUR-COMPUTER-IP:8000`. Find the computer's IPv4 address with `ipconfig` on Windows. Use sample data for this HTTP demo.

## Add a user

```sh
python app.py --add-user REG2026001 --name "Your Name"
```

Enter the phone number when prompted. Use the same country code when signing in.

Run tests with `python test_login.py`.

This is a demo: matching a phone number does not verify ownership.
