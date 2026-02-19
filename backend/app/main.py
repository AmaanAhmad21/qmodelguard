"""QModelGuard FastAPI application."""
import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@app.get("/")
def root():
    """Root info."""
    return {"status": "ok", "app": "QModelGuard"}


@app.get("/health")
def health():
    """Health check for quick testing."""
    return {"status": "ok"}
