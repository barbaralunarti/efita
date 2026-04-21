# backend/app/routers/admin.py
import csv
import io
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.auth import create_access_token, verify_password
from app.config import settings
from app.dependencies import get_current_admin, get_db
from app.models import (
    Admin,
    LogEmail,
    Participante,
    Poster,
    StatusEmail,
    StatusInscricao,
    TipoEmail,
)
from app.schemas import (
    AdminLogin,
    DashboardResponse,
    LogEmailResponse,
    PagamentoUpdate,
    ParticipanteDetail,
    ParticipanteListItem,
    PosterStatusUpdate,
    StatusUpdate,
    TokenResponse,
)
from app.services import participante as svc
from app.services.email import email_service
from app.logger import get_logger

logger = get_logger("app.routers.admin")

router = APIRouter(prefix="/api/admin", tags=["Admin"])

# Limiter específico para proteção de login (brute force)
login_limiter = Limiter(key_func=get_remote_address)


# ── Autenticação ──────────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
@login_limiter.limit("2/5 minutes")
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    logger.info(f"🔐 Tentativa de login - Usuário: {form_data.username}")
    admin = db.query(Admin).filter(Admin.username == form_data.username).first()
    if not admin or not verify_password(form_data.password, admin.password_hash):
        logger.warning(f"❌ Falha na autenticação - Usuário: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
        )
    token = create_access_token({"sub": admin.username})
    logger.info(f"✅ Login bem-sucedido - Usuário: {form_data.username}")
    return TokenResponse(access_token=token)


# ── Dashboard ─────────────────────────────────────────────────────────────────

@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    logger.debug(f"📊 Dashboard acessado - Usuário: {admin.username}")
    stats = svc.get_dashboard_stats(db)
    return DashboardResponse(**stats)


# ── Participantes ─────────────────────────────────────────────────────────────

@router.get("/participantes", response_model=List[ParticipanteListItem])
def listar_participantes(
    status_inscricao: Optional[StatusInscricao] = None,
    categoria: Optional[str] = None,
    is_ita: Optional[bool] = None,
    busca: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    from app.models import Categoria

    logger.info(f"📋 Listando participantes - Filtros: status={status_inscricao}, categoria={categoria}, is_ita={is_ita}, busca={busca}")
    
    cat = None
    if categoria:
        try:
            cat = Categoria(categoria)
        except ValueError:
            logger.warning(f"⚠️  Categoria inválida: {categoria}")
            raise HTTPException(400, "Categoria inválida")

    participantes = svc.listar_participantes(db, status_inscricao, cat, is_ita, busca)
    logger.info(f"✅ {len(participantes)} participantes encontrados")
    return [ParticipanteListItem.from_participante(p) for p in participantes]


@router.get("/participantes/{participante_id}", response_model=ParticipanteDetail)
def detalhe_participante(
    participante_id: int,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    logger.info(f"🔍 Consultando detalhes - Participante ID: {participante_id}")
    p = svc.get_participante_by_id(db, participante_id)
    if not p:
        logger.warning(f"⚠️  Participante não encontrado - ID: {participante_id}")
        raise HTTPException(404, "Participante não encontrado")
    return p


@router.patch("/participantes/{participante_id}/status", response_model=ParticipanteDetail)
def atualizar_status(
    participante_id: int,
    dados: StatusUpdate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    logger.info(f"📝 Atualizando status - Participante ID: {participante_id}, Novo Status: {dados.status_inscricao}")
    p = svc.get_participante_by_id(db, participante_id)
    if not p:
        logger.warning(f"⚠️  Participante não encontrado - ID: {participante_id}")
        raise HTTPException(404, "Participante não encontrado")
    resultado = svc.atualizar_status_inscricao(db, p, dados.status_inscricao)
    logger.info(f"✅ Status atualizado com sucesso - Participante ID: {participante_id}")
    return resultado


@router.patch("/participantes/{participante_id}/pagamento", response_model=ParticipanteDetail)
def atualizar_pagamento(
    participante_id: int,
    dados: PagamentoUpdate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    logger.info(f"💰 Atualizando pagamento - Participante ID: {participante_id}, Novo Status: {dados.status_pagamento}")
    p = svc.get_participante_by_id(db, participante_id)
    if not p:
        logger.warning(f"⚠️  Participante não encontrado - ID: {participante_id}")
        raise HTTPException(404, "Participante não encontrado")
    resultado = svc.atualizar_status_pagamento(db, p, dados.status_pagamento)
    logger.info(f"✅ Pagamento atualizado com sucesso - Participante ID: {participante_id}")
    return resultado


# ── Pôsteres ──────────────────────────────────────────────────────────────────

@router.get("/posters")
def listar_posters(
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    logger.info(f"📊 Listando pôsteres")
    posters = db.query(Poster).all()
    # Adiciona o nome do participante dinamicamente para o frontend
    result = []
    for p in posters:
        result.append({
            "id": p.id,
            "participante_id": p.participante_id,
            "participante_nome": p.participante.nome,
            "titulo": p.titulo,
            "resumo": p.resumo,
            "palavras_chave": p.palavras_chave,
            "status": p.status,
            "created_at": p.created_at
        })
    logger.info(f"✅ {len(result)} pôsteres encontrados")
    return result


@router.patch("/posters/{poster_id}/status")
def atualizar_status_poster(
    poster_id: int,
    dados: PosterStatusUpdate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    logger.info(f"📝 Atualizando status do pôster - ID: {poster_id}, Novo Status: {dados.status}")
    poster = db.query(Poster).filter(Poster.id == poster_id).first()
    if not poster:
        logger.warning(f"⚠️  Pôster não encontrado - ID: {poster_id}")
        raise HTTPException(404, "Pôster não encontrado")
    
    poster.status = dados.status
    db.commit()
    db.refresh(poster)
    logger.info(f"✅ Status do pôster atualizado com sucesso - ID: {poster_id}")
    return {"message": "Status do pôster atualizado com sucesso", "status": poster.status}


# ── E-mails ───────────────────────────────────────────────────────────────────

def _enfileirar_email_participante(participante: Participante, tipo_reenvio: bool = False):
    """Helper que monta e enfileira o e-mail correto para um participante."""
    pid = participante.id
    dest = participante.email

    if participante.is_ita:
        template = "email_aprovado_ita.html"
        subject = "EFITA — Inscrição Confirmada"
    else:
        template = "email_aprovado_externo.html"
        subject = "EFITA — Inscrição Confirmada + Pagamento"

    html = email_service.render_template(
        template,
        participante=participante,
        agenda_url=settings.AGENDA_URL,
        pix_code=settings.PIX_CODE,
    )

    tipo = TipoEmail.REENVIO if tipo_reenvio else (
        TipoEmail.APROVACAO if participante.is_ita else TipoEmail.COBRANCA
    )

    async def on_success():
        from app.database import SessionLocal
        _db = SessionLocal()
        try:
            svc.registrar_log_email(_db, pid, tipo, dest, StatusEmail.ENVIADO)
            logger.info(f"📧 Email de {tipo.value} enviado com sucesso - Participante ID: {pid}")
        finally:
            _db.close()

    async def on_failure(err: str):
        from app.database import SessionLocal
        _db = SessionLocal()
        try:
            svc.registrar_log_email(_db, pid, tipo, dest, StatusEmail.FALHA, err)
            logger.error(f"❌ Falha ao enviar email de {tipo.value} - Participante ID: {pid}, Erro: {err}")
        finally:
            _db.close()

    return html, subject, on_success, on_failure


@router.post("/emails/disparar-lote")
async def disparar_lote(
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    """Enfileira e-mails para todos os aprovados que ainda não receberam."""
    logger.info(f"📧 Iniciando disparo em lote de emails - Usuário: {admin.username}")
    
    aprovados = (
        db.query(Participante)
        .filter(Participante.status_inscricao == StatusInscricao.APROVADO)
        .all()
    )

    sem_email = [
        p for p in aprovados
        if not any(
            e.tipo in (TipoEmail.APROVACAO, TipoEmail.COBRANCA)
            and e.status == StatusEmail.ENVIADO
            for e in p.emails
        )
    ]

    for p in sem_email:
        html, subject, on_success, on_failure = _enfileirar_email_participante(p)
        await email_service.enqueue(p.email, subject, html, on_success, on_failure)

    logger.info(f"✅ {len(sem_email)} emails enfileirados com sucesso")
    return {
        "enfileirados": len(sem_email),
        "mensagem": "E-mails sendo processados em segundo plano",
    }


@router.post("/emails/reenviar/{participante_id}")
async def reenviar_email(
    participante_id: int,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    """Reenvio individual de e-mail de confirmação."""
    logger.info(f"📧 Reenviando email - Participante ID: {participante_id}")
    
    p = svc.get_participante_by_id(db, participante_id)
    if not p or p.status_inscricao != StatusInscricao.APROVADO:
        logger.warning(f"⚠️  Participante não encontrado ou não aprovado - ID: {participante_id}")
        raise HTTPException(404, "Participante não encontrado ou não aprovado")

    html, subject, on_success, on_failure = _enfileirar_email_participante(p, tipo_reenvio=True)
    await email_service.enqueue(p.email, f"[Reenvio] {subject}", html, on_success, on_failure)

    logger.info(f"✅ Email reenfileirado com sucesso - Participante ID: {participante_id}")
    return {"mensagem": "E-mail reenfileirado com sucesso"}


@router.get("/emails/log", response_model=List[LogEmailResponse])
def log_emails(
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    logger.info(f"📋 Consultando log de emails")
    logs = db.query(LogEmail).order_by(LogEmail.enviado_em.desc()).all()
    logger.info(f"✅ {len(logs)} registros de log encontrados")
    return logs


# ── Exportação ────────────────────────────────────────────────────────────────

@router.get("/export/csv")
def exportar_csv(
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    logger.info(f"📥 Exportando participantes em CSV - Usuário: {admin.username}")
    participantes = db.query(Participante).order_by(Participante.created_at).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "ID", "Protocolo", "CPF", "Nome", "E-mail", "Instituição",
            "Categoria", "ITA", "Matrícula ITA", "Status Inscrição",
            "Status Pagamento", "Pôster", "Data Inscrição",
        ]
    )
    for p in participantes:
        writer.writerow(
            [
                p.id,
                f"EFITA-2025-{p.id:05d}",
                p.cpf,
                p.nome,
                p.email,
                p.instituicao,
                p.categoria.value,
                "Sim" if p.is_ita else "Não",
                p.matricula_ita or "",
                p.status_inscricao.value,
                p.status_pagamento.value,
                "Sim" if p.poster else "Não",
                p.created_at.strftime("%Y-%m-%d %H:%M") if p.created_at else "",
            ]
        )

    output.seek(0)
    logger.info(f"✅ CSV exportado com sucesso - {len(participantes)} registros")
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=participantes.csv"},
    )


@router.get("/export/posters/csv")
def exportar_posters_csv(
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    logger.info(f"📥 Exportando pôsteres em CSV - Usuário: {admin.username}")
    posters = db.query(Poster).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "ID Pôster", "ID Participante", "Nome Participante", "E-mail Participante",
            "Título", "Palavras-chave", "Resumo", "Data Submissão"
        ]
    )
    for p in posters:
        writer.writerow(
            [
                p.id,
                p.participante_id,
                p.participante.nome,
                p.participante.email,
                p.titulo,
                p.palavras_chave,
                p.resumo,
                p.created_at.strftime("%Y-%m-%d %H:%M") if p.created_at else "",
            ]
        )

    output.seek(0)
    logger.info(f"✅ CSV de pôsteres exportado com sucesso - {len(posters)} registros")
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=posters.csv"},
    )
