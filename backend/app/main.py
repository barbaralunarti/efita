# backend/app/main.py
from contextlib import asynccontextmanager
import traceback

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.database import SessionLocal, engine
from app.models import Base
from app.routers import admin, inscricao
from app.services.email import email_service
from app.logger import get_logger

logger = get_logger("app.main")

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────
    logger.info("🚀 Iniciando aplicação EFITA...")
    Base.metadata.create_all(bind=engine)
    if settings.EMAILS_ENABLED:
        await email_service.start_worker()
        logger.info("✅ Worker de email iniciado")
    else:
        logger.info("ℹ️  Worker de email NÃO iniciado (feature desabilitada)")
    yield
    # ── Shutdown ─────────────────────────────────────────────
    logger.info("🛑 Encerrando aplicação EFITA...")
    if settings.EMAILS_ENABLED:
        await email_service.stop_worker()
        logger.info("✅ Worker de email encerrado")


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


# Exception handler global para erros não tratados
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Handler global para exceções não tratadas.
    Loga o erro e retorna resposta JSON padronizada.
    """
    logger.error(
        f"❌ Erro não tratado em {request.method} {request.url.path}: {str(exc)}",
        exc_info=exc
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Erro interno do servidor. Por favor, contate o administrador.",
            "error_code": "ERR_INTERNAL_SERVER_ERROR",
        }
    )


@app.get("/health")
def health():
    logger.debug("📊 Health check realizado")
    return {"status": "ok", "queue_size": email_service.queue_size}
