# QModelGuard

Quantum-Safe ML Model Protection — Encrypt and sign machine learning models using post-quantum cryptography.

## Tech Stack

- **Backend:** FastAPI (Python), SQLAlchemy, local filesystem storage for model files
- **Database:** PostgreSQL 16 (Docker Compose). Without `DATABASE_URL`, the backend defaults to a local SQLite file (`backend/qmodelguard.db`) for quick dev.
- **Frontend:** React + Tailwind CSS + React Router
- **Crypto:** qcrypto (Kyber + Dilithium). On **Windows** the app uses **stub crypto** (no liboqs); on Linux/macOS it uses real PQC when liboqs is available.

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

After a fresh clone or after merging branches, always run `npm install` in the frontend folder so all dependencies (React, react-router-dom, Tailwind, Vite, etc.) are installed.

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

## Free Demo Deployment

This setup is intended for a portfolio/demo deployment:

- **Frontend:** Vercel free
- **Backend:** Render free web service
- **Database:** Neon free Postgres
- **File storage:** local Render filesystem for demo only

### 1. Neon Postgres

Create a Neon Postgres database and copy its connection string. The backend already reads `DATABASE_URL` and uses PostgreSQL when it is set.

Use the Neon connection string as:

```bash
DATABASE_URL=postgresql://USER:PASSWORD@HOST/DBNAME?sslmode=require
```

### 2. Render backend

Create a Render **Web Service** for the backend.

Recommended settings:

| Setting | Value |
|---------|-------|
| Runtime | Docker |
| Root directory / Docker context | `backend` |
| Dockerfile path | `backend/Dockerfile` |
| Start command | Use Dockerfile `CMD` |
| Health check path | `/health` |

Required backend environment variables on Render:

```bash
DATABASE_URL=postgresql://USER:PASSWORD@HOST/DBNAME?sslmode=require
JWT_SECRET=replace-with-a-strong-random-secret
CORS_ORIGINS=https://YOUR-VERCEL-APP.vercel.app
STORAGE_DIR=/app/app/storage
MAX_MODEL_SIZE_MB=25
```

Recommended:

```bash
KEY_ENCRYPTION_KEY=replace-with-a-fernet-key
```

Generate a Fernet key with:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

The backend Dockerfile binds uvicorn to Render's `PORT` environment variable when Render provides one, and falls back to port `8000` locally.

### 3. Vercel frontend

Deploy the frontend on Vercel.

Recommended settings:

| Setting | Value |
|---------|-------|
| Root directory | `frontend` |
| Build command | `npm run build` |
| Output directory | `dist` |

The frontend uses relative `/api` and `/health` requests. `frontend/vercel.json` rewrites those requests to the Render backend, so `VITE_API_URL` is not required.

Before deploying, replace this placeholder in `frontend/vercel.json`:

```text
https://REPLACE_WITH_RENDER_BACKEND_URL
```

with your Render backend URL, for example:

```text
https://qmodelguard-backend.onrender.com
```

### Demo limitations

On Render free, local filesystem storage is not durable. Uploaded model files may disappear after restarts, deploys, rebuilds, or instance replacement. Neon will keep the database rows, so a model record can remain even if the file is gone.

`qcrypto` may run in stub mode if liboqs is not available in the Render environment. The app remains functional either way. After deployment, check:

```text
https://YOUR-RENDER-BACKEND.onrender.com/health
```

Confirm `database` and `storage` are `ok`, and check whether `crypto` reports `real` or `stub`.

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

### Database

- **Docker (recommended full stack):** From the repo root, `docker compose up` runs PostgreSQL and sets `DATABASE_URL` for the backend (see `docker-compose.yml`). Tables are created on startup.
- **Local Python only:** If `DATABASE_URL` is not set, the backend uses SQLite at `backend/qmodelguard.db` and creates tables automatically. For PostgreSQL locally, set `DATABASE_URL` to a `postgresql://...` connection string (see `requirements.txt` / `psycopg2-binary`).

### Crypto: stub mode on Windows

On **Windows**, the backend does **not** load liboqs (to avoid failed auto-install). Encrypt/decrypt/sign/verify still work using **stub implementations** so you can run and test the full flow. For **real** post-quantum crypto (Kyber/Dilithium), run the backend on **Linux or macOS** (or WSL), where liboqs can be built and used.

## Demo flow for presentation

Use this sequence for a live demo or to verify the full flow. Backend must be running at `http://localhost:8000`. Use any small `.pt` file (e.g. a few KB) or create one: `echo "dummy" > demo.pt` (may need to be valid PyTorch for real use; for API demo the backend only checks extension).

**1. Show API and crypto mode (for slides)**  
- Open **http://localhost:8000** — shows app name, version, links to `/docs` and `/health`.  
- Open **http://localhost:8000/health** — shows `crypto: "real"` or `"stub"`, plus `algorithms: { kem: "Kyber768", sig: "Dilithium3" }`. Use this to say “we’re running real post-quantum crypto” (or explain stub on Windows).

**2. Register two users (Alice, Bob)**  
```bash
curl -s -X POST http://localhost:8000/api/users/register -H "Content-Type: application/json" -d '{"username":"alice","password":"pass123"}'
curl -s -X POST http://localhost:8000/api/users/register -H "Content-Type: application/json" -d '{"username":"bob","password":"pass123"}'
```
Save tokens from the JSON responses (`token` and `user_id`). Or login to get a token:
```bash
ALICE=$(curl -s -X POST http://localhost:8000/api/users/login -H "Content-Type: application/json" -d '{"username":"alice","password":"pass123"}' | jq -r '.token')
BOB=$(curl -s -X POST http://localhost:8000/api/users/login -H "Content-Type: application/json" -d '{"username":"bob","password":"pass123"}' | jq -r '.token')
```

**3. Alice: upload a model**  
```bash
curl -s -X POST http://localhost:8000/api/models/upload -H "Authorization: Bearer $ALICE" -F "file=@demo.pt"
```
Note the returned `id` (e.g. `MODEL_ID=1`).

**4. Alice: sign the model**  
```bash
curl -s -X POST http://localhost:8000/api/models/sign -H "Authorization: Bearer $ALICE" -H "Content-Type: application/json" -d "{\"model_id\": $MODEL_ID}"
```
Save the returned `signature_b64` for the verify step.

**5. Alice: encrypt for Bob**  
```bash
curl -s -X POST http://localhost:8000/api/models/encrypt -H "Authorization: Bearer $ALICE" -H "Content-Type: application/json" -d "{\"model_id\": $MODEL_ID, \"recipient_id\": \"bob\"}"
```
Note `encrypted_model_id` (Bob’s copy of the encrypted file).

**6. Bob: decrypt**  
```bash
curl -s -X POST http://localhost:8000/api/models/decrypt -H "Authorization: Bearer $BOB" -H "Content-Type: application/json" -d "{\"model_id\": $ENCRYPTED_MODEL_ID}"
```
Returns `decrypted_model_id`. Bob can download the file via `GET /api/models/{id}`.

**7. Bob: verify signature (proves Alice signed the original)**  
Verification is over the *plaintext* file, so use the decrypted model id from step 6:
```bash
curl -s -X POST http://localhost:8000/api/models/verify -H "Authorization: Bearer $BOB" -H "Content-Type: application/json" -d "{\"model_id\": $DECRYPTED_MODEL_ID, \"signer_id\": \"alice\", \"signature_b64\": \"$SIGNATURE_B64\"}"
```
Returns `{"valid": true}` when the signature is valid.

**8. Interactive API docs**  
Open **http://localhost:8000/docs** to show and try all endpoints with “Authorize” (paste a JWT).

## Project Structure

```
QModelGuard/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app
│   │   ├── api/             # Routers (keys, models, users)
│   │   ├── services/        # qcrypto + file storage stubs
│   │   └── db/              # SQLAlchemy models + session (Postgres or SQLite)
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

## API Endpoints

| Method | Endpoint                | Description            |
|--------|-------------------------|------------------------|
| POST   | /api/keys/generate      | Generate new keypair   |
| GET    | /api/keys/public        | Get your public key    |
| GET    | /api/keys/public/{id}   | Get another user's key |
| GET    | /api/models             | List your models       |
| POST   | /api/models/upload      | Upload model file      |
| GET    | /api/models/{id}        | Download model file    |
| DELETE | /api/models/{id}        | Delete your model      |
| POST   | /api/models/encrypt     | Encrypt for recipient  |
| POST   | /api/models/decrypt     | Decrypt with your key  |
| POST   | /api/models/sign        | Sign model             |
| POST   | /api/models/verify      | Verify signature       |
| POST   | /api/users/register     | Register (rate limited)|
| POST   | /api/users/login        | Login (rate limited)   |
| GET    | /api/users/me           | Current user           |
| GET    | /api/users/list         | List users (for Encrypt for…) |

Auth uses JWT; register/login/upload are rate limited per IP. See `backend/.env.example` for JWT_SECRET and optional KEY_ENCRYPTION_KEY.
