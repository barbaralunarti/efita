# backend/app/services/participante.py
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import (
    Categoria,
    LogEmail,
    Participante,
    Poster,
    StatusEmail,
    StatusInscricao,
    StatusPagamento,
    TipoEmail,
)
from app.schemas import InscricaoCreate


def criar_participante(db: Session, dados: InscricaoCreate) -> Participante:
    """Cria um participante (e pôster opcional) no banco."""
    is_ita = dados.instituicao.strip().upper() == "ITA"

    # Participantes ITA não precisam pagar
    status_pag = StatusPagamento.NAO_APLICAVEL if is_ita else StatusPagamento.PENDENTE

    participante = Participante(
        cpf=dados.cpf,
        nome=dados.nome,
        email=dados.email,
        instituicao=dados.instituicao,
        matricula_ita=dados.matricula_ita,
        categoria=dados.categoria,
        is_ita=is_ita,
        status_inscricao=StatusInscricao.PENDENTE,
        status_pagamento=status_pag,
    )
    db.add(participante)
    db.flush()  # gera o ID sem commitar

    if dados.poster:
        poster = Poster(
            participante_id=participante.id,
            titulo=dados.poster.titulo,
            resumo=dados.poster.resumo,
            palavras_chave=dados.poster.palavras_chave,
        )
        db.add(poster)

    db.commit()
    db.refresh(participante)
    return participante


def registrar_log_email(
    db: Session,
    participante_id: int,
    tipo: TipoEmail,
    destinatario: str,
    status: StatusEmail,
    erro: Optional[str] = None,
) -> LogEmail:
    log = LogEmail(
        participante_id=participante_id,
        tipo=tipo,
        destinatario=destinatario,
        status=status,
        erro=erro,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_participante_by_cpf(db: Session, cpf: str) -> Optional[Participante]:
    return db.query(Participante).filter(Participante.cpf == cpf).first()


def get_participante_by_id(db: Session, participante_id: int) -> Optional[Participante]:
    return db.get(Participante, participante_id)


def listar_participantes(
    db: Session,
    status: Optional[StatusInscricao] = None,
    categoria: Optional[Categoria] = None,
    is_ita: Optional[bool] = None,
    busca: Optional[str] = None,
) -> List[Participante]:
    q = db.query(Participante)
    if status:
        q = q.filter(Participante.status_inscricao == status)
    if categoria:
        q = q.filter(Participante.categoria == categoria)
    if is_ita is not None:
        q = q.filter(Participante.is_ita == is_ita)
    if busca:
        like = f"%{busca}%"
        q = q.filter(
            (Participante.nome.ilike(like)) | (Participante.cpf.ilike(like))
        )
    return q.order_by(Participante.created_at.desc()).all()


def atualizar_status_inscricao(
    db: Session, participante: Participante, novo_status: StatusInscricao
) -> Participante:
    participante.status_inscricao = novo_status

    # Ao aprovar externo, muda pagamento para PENDENTE (se ainda não pago)
    if novo_status == StatusInscricao.APROVADO and not participante.is_ita:
        if participante.status_pagamento == StatusPagamento.NAO_APLICAVEL:
            participante.status_pagamento = StatusPagamento.PENDENTE

    participante.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(participante)
    return participante


def atualizar_status_pagamento(
    db: Session, participante: Participante, novo_status: StatusPagamento
) -> Participante:
    participante.status_pagamento = novo_status
    participante.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(participante)
    return participante


def get_dashboard_stats(db: Session) -> dict:
    from app.models import LogEmail, Poster, StatusEmail

    total = db.query(Participante).count()
    pendentes = db.query(Participante).filter(Participante.status_inscricao == StatusInscricao.PENDENTE).count()
    aprovados = db.query(Participante).filter(Participante.status_inscricao == StatusInscricao.APROVADO).count()
    recusados = db.query(Participante).filter(Participante.status_inscricao == StatusInscricao.RECUSADO).count()
    total_ita = db.query(Participante).filter(Participante.is_ita == True).count()
    total_externos = db.query(Participante).filter(Participante.is_ita == False).count()
    pag_pendentes = db.query(Participante).filter(Participante.status_pagamento == StatusPagamento.PENDENTE).count()
    pag_confirmados = db.query(Participante).filter(Participante.status_pagamento == StatusPagamento.PAGO).count()
    total_posters = db.query(Poster).count()
    emails_enviados = db.query(LogEmail).filter(LogEmail.status == StatusEmail.ENVIADO).count()
    emails_falha = db.query(LogEmail).filter(LogEmail.status == StatusEmail.FALHA).count()

    return {
        "total_inscritos": total,
        "pendentes": pendentes,
        "aprovados": aprovados,
        "recusados": recusados,
        "total_ita": total_ita,
        "total_externos": total_externos,
        "pagamentos_pendentes": pag_pendentes,
        "pagamentos_confirmados": pag_confirmados,
        "total_posters": total_posters,
        "emails_enviados": emails_enviados,
        "emails_falha": emails_falha,
    }
