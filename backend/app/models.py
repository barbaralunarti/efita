# backend/app/models.py
import enum
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, relationship


# ── Enums ─────────────────────────────────────────────────────────────────────

class Categoria(str, enum.Enum):
    GRADUACAO = "graduacao"
    POS_GRADUACAO = "pos_graduacao"
    PROFESSOR = "professor"
    PROFISSIONAL = "profissional"


class StatusInscricao(str, enum.Enum):
    PENDENTE = "pendente"
    APROVADO = "aprovado"
    RECUSADO = "recusado"


class StatusPagamento(str, enum.Enum):
    NAO_APLICAVEL = "nao_aplicavel"   # participantes ITA
    PENDENTE = "pendente"             # externos aprovados
    PAGO = "pago"                     # validado pela coordenação


class StatusPoster(str, enum.Enum):
    PENDENTE = "pendente"
    APROVADO = "aprovado"
    RECUSADO = "recusado"


class TipoEmail(str, enum.Enum):
    RECEBIMENTO = "recebimento"   # enviado imediatamente após submissão
    APROVACAO = "aprovacao"
    COBRANCA = "cobranca"
    REENVIO = "reenvio"


class StatusEmail(str, enum.Enum):
    ENVIADO = "enviado"
    FALHA = "falha"


# ── Base ──────────────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


# ── Modelos ───────────────────────────────────────────────────────────────────

def _now():
    return datetime.now(timezone.utc)


class Participante(Base):
    __tablename__ = "participantes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cpf = Column(String(11), unique=True, nullable=False, index=True)
    nome = Column(String(200), nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    instituicao = Column(String(200), nullable=False)
    matricula_ita = Column(String(20), nullable=True)
    categoria = Column(Enum(Categoria), nullable=False)
    is_ita = Column(Boolean, default=False, nullable=False)
    status_inscricao = Column(
        Enum(StatusInscricao), default=StatusInscricao.PENDENTE, nullable=False
    )
    status_pagamento = Column(
        Enum(StatusPagamento), default=StatusPagamento.PENDENTE, nullable=False
    )
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    poster = relationship("Poster", back_populates="participante", uselist=False)
    emails = relationship("LogEmail", back_populates="participante")


class Poster(Base):
    __tablename__ = "posters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    participante_id = Column(
        Integer, ForeignKey("participantes.id"), unique=True, nullable=False
    )
    titulo = Column(String(300), nullable=False)
    resumo = Column(Text, nullable=False)
    palavras_chave = Column(String(500), nullable=False)
    status = Column(Enum(StatusPoster), default=StatusPoster.PENDENTE, nullable=False)
    created_at = Column(DateTime, default=_now)

    participante = relationship("Participante", back_populates="poster")


class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=_now)


class LogEmail(Base):
    __tablename__ = "log_emails"

    id = Column(Integer, primary_key=True, autoincrement=True)
    participante_id = Column(Integer, ForeignKey("participantes.id"), nullable=False)
    tipo = Column(Enum(TipoEmail), nullable=False)
    destinatario = Column(String(200), nullable=False)
    status = Column(Enum(StatusEmail), nullable=False)
    erro = Column(Text, nullable=True)
    enviado_em = Column(DateTime, default=_now)

    participante = relationship("Participante", back_populates="emails")
