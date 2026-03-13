"""QModelGuard FastAPI application."""
import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

load_dotenv()

from app.api import keys, models, users
from app.db.database import init_db, DB_PATH
from app.services.storage import ensure_storage_dir, get_storage_path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CORS_ORIGINS = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
    if o.strip()
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: ensure paths exist, init DB safely. Shutdown: cleanup if needed."""
    ensure_storage_dir()
    logger.info("DB path: %s", DB_PATH.resolve())
    logger.info("Storage path: %s", get_storage_path())
    try:
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error("Failed to init database: %s", e)
        raise
    yield


app = FastAPI(
    title="QModelGuard API",
    description="Quantum-Safe ML Model Protection",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(keys.router, prefix="/api/keys", tags=["keys"])
app.include_router(models.router, prefix="/api/models", tags=["models"])
app.include_router(users.router, prefix="/api/users", tags=["users"])


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Return 500 with a safe message; log the real error."""
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."},
    )


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    """Avoid 404 when browser requests favicon (e.g. opening API root)."""
    return Response(status_code=204)


@app.get("/")
def root():
    """Root info."""
    return {"status": "ok", "app": "QModelGuard"}


@app.get("/health")
def health():
    """Health check: status, DB connectivity, storage dir writable."""
    from sqlalchemy import text
    out = {"status": "ok"}
    try:
        from app.db.database import engine
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        out["database"] = "ok"
    except Exception as e:
        out["database"] = str(e)
    try:
        from app.services.storage import ensure_storage_dir, get_storage_path
        ensure_storage_dir()
        p = get_storage_path()
        out["storage"] = "ok" if p.exists() else "missing"
    except Exception as e:
        out["storage"] = str(e)
    return out
