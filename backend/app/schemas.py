# backend/app/schemas.py
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator, model_validator

from app.models import Categoria, StatusEmail, StatusInscricao, StatusPagamento, StatusPoster, TipoEmail


# ── Poster ────────────────────────────────────────────────────────────────────

class PosterCreate(BaseModel):
    titulo: str
    resumo: str
    palavras_chave: str

    @field_validator("titulo")
    @classmethod
    def titulo_max(cls, v: str) -> str:
        if len(v) > 300:
            raise ValueError("Título deve ter no máximo 300 caracteres")
        return v

    @field_validator("resumo")
    @classmethod
    def resumo_max(cls, v: str) -> str:
        if len(v) > 3000:
            raise ValueError("Resumo deve ter no máximo 3000 caracteres")
        return v

    @field_validator("palavras_chave")
    @classmethod
    def palavras_max(cls, v: str) -> str:
        if len(v) > 500:
            raise ValueError("Palavras-chave devem ter no máximo 500 caracteres")
        return v


class PosterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str
    resumo: str
    palavras_chave: str
    status: StatusPoster
    created_at: datetime


class PosterStatusUpdate(BaseModel):
    status: StatusPoster


# ── Inscrição ─────────────────────────────────────────────────────────────────

class InscricaoCreate(BaseModel):
    cpf: str
    nome: str
    email: EmailStr
    instituicao: str
    matricula_ita: Optional[str] = None
    categoria: Categoria
    poster: Optional[PosterCreate] = None

    @field_validator("cpf")
    @classmethod
    def validar_cpf(cls, v: str) -> str:
        digits = "".join(c for c in v if c.isdigit())
        if len(digits) != 11:
            raise ValueError("CPF deve conter 11 dígitos")
        return digits

    @model_validator(mode="after")
    def validar_matricula(self) -> "InscricaoCreate":
        is_ita = self.instituicao.strip().upper() == "ITA"
        precisa = self.categoria in (Categoria.GRADUACAO, Categoria.POS_GRADUACAO)
        if is_ita and precisa and not self.matricula_ita:
            raise ValueError(
                "Matrícula obrigatória para alunos de graduação e pós-graduação do ITA"
            )
        return self


class InscricaoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    protocolo: str
    cpf_mascarado: str
    nome: str
    email: str
    instituicao: str
    categoria: Categoria
    is_ita: bool
    status_inscricao: StatusInscricao
    status_pagamento: StatusPagamento
    tem_poster: bool
    status_poster: Optional[StatusPoster] = None
    created_at: datetime

    @classmethod
    def from_participante(cls, p) -> "InscricaoResponse":
        return cls(
            id=p.id,
            protocolo=f"EFITA-2025-{p.id:05d}",
            cpf_mascarado=f"***.***.*{p.cpf[-2:]}",  # mostra apenas 2 últimos dígitos
            nome=p.nome,
            email=p.email,
            instituicao=p.instituicao,
            categoria=p.categoria,
            is_ita=p.is_ita,
            status_inscricao=p.status_inscricao,
            status_pagamento=p.status_pagamento,
            tem_poster=p.poster is not None,
            status_poster=p.poster.status if p.poster else None,
            created_at=p.created_at,
        )


# ── Admin ─────────────────────────────────────────────────────────────────────

class AdminLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── Status updates ────────────────────────────────────────────────────────────

class StatusUpdate(BaseModel):
    status_inscricao: StatusInscricao


class PagamentoUpdate(BaseModel):
    status_pagamento: StatusPagamento


# ── Participante (admin view) ─────────────────────────────────────────────────

class LogEmailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tipo: TipoEmail
    destinatario: str
    status: StatusEmail
    erro: Optional[str]
    enviado_em: datetime


class ParticipanteDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cpf: str
    nome: str
    email: str
    instituicao: str
    matricula_ita: Optional[str]
    categoria: Categoria
    is_ita: bool
    status_inscricao: StatusInscricao
    status_pagamento: StatusPagamento
    created_at: datetime
    updated_at: Optional[datetime]
    poster: Optional[PosterResponse]
    emails: List[LogEmailResponse]


class ParticipanteListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    email: str
    cpf: str
    instituicao: str
    categoria: Categoria
    is_ita: bool
    status_inscricao: StatusInscricao
    status_pagamento: StatusPagamento
    tem_poster: bool
    created_at: datetime

    @classmethod
    def from_participante(cls, p) -> "ParticipanteListItem":
        return cls(
            id=p.id,
            nome=p.nome,
            email=p.email,
            cpf=p.cpf,
            instituicao=p.instituicao,
            categoria=p.categoria,
            is_ita=p.is_ita,
            status_inscricao=p.status_inscricao,
            status_pagamento=p.status_pagamento,
            tem_poster=p.poster is not None,
            created_at=p.created_at,
        )


# ── Dashboard ─────────────────────────────────────────────────────────────────

class DashboardResponse(BaseModel):
    total_inscritos: int
    pendentes: int
    aprovados: int
    recusados: int
    total_ita: int
    total_externos: int
    pagamentos_pendentes: int
    pagamentos_confirmados: int
    total_posters: int
    emails_enviados: int
    emails_falha: int
