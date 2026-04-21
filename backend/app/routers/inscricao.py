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
        participante = svc.criar_participante(db, dados)
    except IntegrityError:
        db.rollback()
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
        finally:
            _db.close()

    async def on_failure(err: str):
        from app.database import SessionLocal
        _db = SessionLocal()
        try:
            svc.registrar_log_email(_db, pid, TipoEmail.RECEBIMENTO, dest, StatusEmail.FALHA, err)
        finally:
            _db.close()

    await email_service.enqueue(dest, "EFITA — Recebemos sua inscrição", html, on_success, on_failure)

    return InscricaoResponse.from_participante(participante)


@router.get("/{cpf}", response_model=InscricaoResponse)
def consultar_inscricao(cpf: str, db: Session = Depends(get_db)):
    """Consulta pública do status da inscrição pelo CPF."""
    digits = "".join(c for c in cpf if c.isdigit())
    participante = svc.get_participante_by_cpf(db, digits)
    if not participante:
        raise HTTPException(status_code=404, detail="Inscrição não encontrada")
    return InscricaoResponse.from_participante(participante)
