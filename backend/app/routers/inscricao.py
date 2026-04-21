# backend/app/routers/inscricao.py
import csv
import io
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.config import settings
from app.dependencies import get_db
from app.models import LogEmail, StatusEmail, TipoEmail
from app.schemas import InscricaoCreate, InscricaoResponse
from app.services import participante as svc
from app.services.email import email_service
from app.logger import get_logger

logger = get_logger("app.routers.inscricao")

router = APIRouter(prefix="/api/inscricao", tags=["Inscrição"])
limiter = Limiter(key_func=get_remote_address)


@router.post("", response_model=InscricaoResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def criar_inscricao(
    request: Request,
    dados: InscricaoCreate,
    db: Session = Depends(get_db),
):
    """Cria nova inscrição e enfileira e-mail de recebimento."""
    from sqlalchemy.exc import IntegrityError

    try:
        logger.info(f"📝 Criando inscrição - CPF: {dados.cpf[:3]}***")
        participante = svc.criar_participante(db, dados)
        logger.info(f"✅ Inscrição criada com sucesso - ID: {participante.id}, Email: {participante.email}")
    except IntegrityError:
        db.rollback()
        logger.warning(f"⚠️  Inscrição duplicada - CPF ou Email já cadastrado")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="CPF ou e-mail já cadastrado",
        )

    # Enfileira e-mail de recebimento assincronamente
    pid = participante.id
    dest = participante.email

    html = email_service.render_template(
        "email_recebimento.html",
        participante=participante,
    )

    async def on_success():
        from app.database import SessionLocal
        _db = SessionLocal()
        try:
            svc.registrar_log_email(_db, pid, TipoEmail.RECEBIMENTO, dest, StatusEmail.ENVIADO)
            logger.info(f"📧 Email de recebimento enviado - Participante ID: {pid}")
        finally:
            _db.close()

    async def on_failure(err: str):
        from app.database import SessionLocal
        _db = SessionLocal()
        try:
            svc.registrar_log_email(_db, pid, TipoEmail.RECEBIMENTO, dest, StatusEmail.FALHA, err)
            logger.error(f"❌ Falha ao enviar email de recebimento - Participante ID: {pid}, Erro: {err}")
        finally:
            _db.close()

    await email_service.enqueue(dest, "EFITA — Recebemos sua inscrição", html, on_success, on_failure)

    return InscricaoResponse.from_participante(participante)


@router.get("/{cpf}", response_model=InscricaoResponse)
def consultar_inscricao(cpf: str, db: Session = Depends(get_db)):
    """Consulta pública do status da inscrição pelo CPF."""
    logger.info(f"🔍 Consultando inscrição - CPF: {cpf[:3]}***")
    digits = "".join(c for c in cpf if c.isdigit())
    participante = svc.get_participante_by_cpf(db, digits)
    if not participante:
        logger.warning(f"⚠️  Inscrição não encontrada - CPF: {cpf[:3]}***")
        raise HTTPException(status_code=404, detail="Inscrição não encontrada")
    logger.info(f"✅ Inscrição consultada com sucesso - ID: {participante.id}, Status: {participante.status_inscricao}")
    return InscricaoResponse.from_participante(participante)
