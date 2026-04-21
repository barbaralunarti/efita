# backend/app/main.py
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.database import SessionLocal, engine
from app.models import Base
from app.routers import admin, inscricao
from app.services.email import email_service

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────
    Base.metadata.create_all(bind=engine)
    await email_service.start_worker()
    yield
    # ── Shutdown ─────────────────────────────────────────────
    await email_service.stop_worker()


app = FastAPI(
    title="EFITA — Sistema de Gestão de Inscrições",
    version="1.0.0",
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(inscricao.router)
app.include_router(admin.router)


@app.get("/health")
def health():
    return {"status": "ok", "queue_size": email_service.queue_size}
