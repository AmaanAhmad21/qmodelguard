# QModelGuard

Quantum-Safe ML Model Protection — Encrypt and sign machine learning models using post-quantum cryptography.

## Tech Stack

- **Backend:** FastAPI (Python), SQLite, local filesystem storage
- **Frontend:** React + Tailwind CSS
- **Crypto:** qcrypto (stubbed; to be implemented)

## Quick Start (Clone and Run)

### 1. Clone

```bash
git clone <repo-url>
cd qmodelguard
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
```

Activate the virtual environment:

- **Windows (Git Bash):** `source venv/Scripts/activate`
- **Windows (cmd):** `venv\Scripts\activate`
- **Windows (PowerShell):** `venv\Scripts\Activate.ps1`
- **macOS / Linux:** `source venv/bin/activate`

Then:

```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

> Use `python -m uvicorn` (not `uvicorn` directly) so it works even if the venv activate script has path issues.

Backend runs at **http://localhost:8000**

### 3. Frontend Setup

Open a **new terminal** (keep the backend running):

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at **http://localhost:3000**. Tailwind CSS v3 is pinned; do not upgrade to v4 (it requires a different PostCSS setup).

### 4. URLs to Open

| App      | URL                      |
|----------|--------------------------|
| Frontend | http://localhost:3000    |
| Backend  | http://localhost:8000    |
| API docs | http://localhost:8000/docs |

The frontend proxies `/api` to the backend, so API calls work from the React app.

## Convenience Scripts (Root)

From the project root (`qmodelguard/`), after `npm install` (installs `concurrently`):

```bash
# Run frontend only
npm run dev:frontend

# Run backend (requires venv activated in this terminal first)
cd backend && source venv/Scripts/activate   # Git Bash
# or: cd backend && venv\Scripts\activate    # Windows cmd
npm run dev:backend

# Run both backend + frontend (activate backend venv first)
npm run dev
```

## Configuration

Optional env overrides (defaults work for local dev):

- **Backend:** Copy `backend/.env.example` → `backend/.env`
- **Frontend:** Copy `frontend/.env.example` → `frontend/.env`

| Variable              | Default                     | Description                    |
|-----------------------|-----------------------------|--------------------------------|
| `CORS_ORIGINS`        | `http://localhost:3000,...` | Allowed CORS origins           |
| `VITE_API_PROXY_TARGET` | `http://localhost:8000`   | Backend URL for frontend proxy |

## Common Errors & Fixes

### Port already in use

- **Backend (8000):** Another process is using port 8000. Stop it or use a different port:
  ```bash
  python -m uvicorn app.main:app --reload --port 8001
  ```
  If you change the port, set `VITE_API_PROXY_TARGET=http://localhost:8001` in `frontend/.env` (or create it from `.env.example`).

- **Frontend (3000):** Change port in `frontend/vite.config.js` (`server.port`) or run:
  ```bash
  npm run dev -- --port 3001
  ```
  Then add `http://localhost:3001` to backend `CORS_ORIGINS` in `backend/.env`.

### ModuleNotFoundError / "No module named 'app'"

You are not in the `backend` folder, or the venv is not activated. Run:

```bash
cd backend
# Activate venv first (see step 2 above)
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

### venv not found / "python" not recognized

- Create a venv: `python -m venv venv`
- If `python` fails, try `python3` or install Python from [python.org](https://python.org) (3.10+).

### Fatal error in launcher / pip or uvicorn not found after clone

The venv stores absolute paths. If you cloned or moved the repo, the venv may be broken. Delete and recreate it:

```bash
cd backend
rm -rf venv          # or: rmdir /s venv  (Windows cmd)
python -m venv venv
source venv/Scripts/activate   # Git Bash (Windows)
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

### Frontend: ECONNREFUSED / proxy error for /health

The frontend proxies `/api` and `/health` to the backend. Start the backend first (step 2), then the frontend. If the backend is not running on port 8000, you'll see connection refused.

### Tailwind PostCSS / "Cannot find module 'tailwindcss'" or v4 plugin error

Ensure `tailwindcss`, `postcss`, and `autoprefixer` are in `frontend/package.json` devDependencies. Tailwind must be v3 (not v4). If you see v4 errors:

```bash
cd frontend
npm install -D tailwindcss@3 postcss autoprefixer
npm run dev
```

### Node / npm version issues

- Use Node 18+ (LTS recommended): `node -v`
- Install Node from [nodejs.org](https://nodejs.org) or via nvm/fnm.

### SQLite / Database

The backend creates `backend/qmodelguard.db` and tables automatically on first startup. No manual setup required.

## Project Structure

```
QModelGuard/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app
│   │   ├── api/             # Routers (keys, models, users)
│   │   ├── services/        # qcrypto + file storage stubs
│   │   └── db/              # SQLite models + session
│   ├── tests/
│   └── requirements.txt
├── frontend/                # React + Tailwind + Vite
└── README.md
```

## Run Tests

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

## API Endpoints (Stub)

| Method | Endpoint                | Description            |
|--------|-------------------------|------------------------|
| POST   | /api/keys/generate      | Generate new keypair   |
| GET    | /api/keys/public        | Get your public key    |
| GET    | /api/keys/public/{id}   | Get another user's key |
| POST   | /api/models/upload      | Upload model file      |
| GET    | /api/models/{id}        | Download model file    |
| POST   | /api/models/encrypt     | Encrypt for recipient  |
| POST   | /api/models/decrypt     | Decrypt with your key  |
| POST   | /api/models/sign        | Sign model             |
| POST   | /api/models/verify      | Verify signature       |
| POST   | /api/users/register     | Register               |
| POST   | /api/users/login        | Login                  |

Crypto and auth are stubbed; implement in `backend/app/services/qcrypto.py` and route logic.
