# NEXUS Among Us Dashboard

Event dashboard built with React, TypeScript, Express, and Socket.IO. This branch also includes a standalone Python login page.

## Python login

Requires Python 3.10+ with no extra packages.

```sh
python python-login/app.py
```

Open http://127.0.0.1:8000. Demo login: `CREW001` / `9876543210`.

See [login setup](python-login/README.md) for phone access and adding users. The login demo runs separately from the dashboard.

## Dashboard setup

Requires Node.js 20+ and npm. From the repository folder:

```sh
npm run install:all
```

Copy `backend/.env.example` to `backend/.env` and `frontend/.env.example` to `frontend/.env`, then run:

```sh
npm run dev
```

Frontend: http://localhost:5173. Backend: http://localhost:5000.

Build with `npm run build`.

## Documentation

- [API](docs/API_SPECS.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Contributing](CONTRIBUTING.md)

[MIT License](LICENSE).
