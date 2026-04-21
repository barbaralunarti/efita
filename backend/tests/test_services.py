# backend/tests/test_services.py
"""Testes unitários para a camada de serviço (lógica de negócio)."""
import pytest

from app.models import (
    Categoria,
    StatusInscricao,
    StatusPagamento,
    StatusEmail,
    TipoEmail,
)
from app.schemas import InscricaoCreate, PosterCreate
from app.services import participante as svc


# ── Criação de participantes ───────────────────────────────────────────────────

class TestCriarParticipante:
    def test_externo_tem_pagamento_pendente(self, db):
        dados = InscricaoCreate(
            cpf="12345678901",
            nome="Externo",
            email="ext@test.com",
            instituicao="USP",
            categoria=Categoria.GRADUACAO,
        )
        p = svc.criar_participante(db, dados)
        assert p.is_ita is False
        assert p.status_pagamento == StatusPagamento.PENDENTE
        assert p.status_inscricao == StatusInscricao.PENDENTE

    def test_ita_tem_pagamento_nao_aplicavel(self, db):
        dados = InscricaoCreate(
            cpf="11122233344",
            nome="ITA",
            email="ita@ita.br",
            instituicao="ITA",
            matricula_ita="GE123",
            categoria=Categoria.GRADUACAO,
        )
        p = svc.criar_participante(db, dados)
        assert p.is_ita is True
        assert p.status_pagamento == StatusPagamento.NAO_APLICAVEL

    def test_ita_maiusculo_minusculo(self, db):
        """'ita' (minúsculo) deve ser reconhecido como ITA."""
        dados = InscricaoCreate(
            cpf="55566677788",
            nome="ITA min",
            email="itamin@ita.br",
            instituicao="  ita  ",
            matricula_ita="GE999",
            categoria=Categoria.GRADUACAO,
        )
        p = svc.criar_participante(db, dados)
        assert p.is_ita is True

    def test_com_poster(self, db):
        dados = InscricaoCreate(
            cpf="98765432109",
            nome="Com Poster",
            email="poster@test.com",
            instituicao="UNICAMP",
            categoria=Categoria.PROFISSIONAL,
            poster=PosterCreate(
                titulo="Meu Pôster",
                resumo="Resumo detalhado",
                palavras_chave="física, quântica",
            ),
        )
        p = svc.criar_participante(db, dados)
        db.refresh(p)
        assert p.poster is not None
        assert p.poster.titulo == "Meu Pôster"

    def test_sem_poster(self, db):
        dados = InscricaoCreate(
            cpf="10101010101",
            nome="Sem Poster",
            email="sempost@test.com",
            instituicao="UNESP",
            categoria=Categoria.PROFESSOR,
        )
        p = svc.criar_participante(db, dados)
        db.refresh(p)
        assert p.poster is None


# ── Atualização de status ─────────────────────────────────────────────────────

class TestAtualizarStatus:
    def _criar(self, db, suffix=""):
        dados = InscricaoCreate(
            cpf=f"1234567890{suffix}",
            nome=f"Participante{suffix}",
            email=f"p{suffix}@test.com",
            instituicao="USP",
            categoria=Categoria.PROFISSIONAL,
        )
        return svc.criar_participante(db, dados)

    def test_aprovar_externo_muda_pagamento(self, db):
        p = self._criar(db, "1")
        svc.atualizar_status_inscricao(db, p, StatusInscricao.APROVADO)
        assert p.status_inscricao == StatusInscricao.APROVADO
        assert p.status_pagamento == StatusPagamento.PENDENTE

    def test_recusar_nao_muda_pagamento(self, db):
        p = self._criar(db, "2")
        svc.atualizar_status_inscricao(db, p, StatusInscricao.RECUSADO)
        assert p.status_inscricao == StatusInscricao.RECUSADO
        assert p.status_pagamento == StatusPagamento.PENDENTE  # permanece

    def test_aprovar_ita_nao_muda_pagamento(self, db):
        dados = InscricaoCreate(
            cpf="22233344455",
            nome="ITA Srv",
            email="itasrv@ita.br",
            instituicao="ITA",
            categoria=Categoria.PROFESSOR,
        )
        p = svc.criar_participante(db, dados)
        svc.atualizar_status_inscricao(db, p, StatusInscricao.APROVADO)
        assert p.status_pagamento == StatusPagamento.NAO_APLICAVEL


# ── Log de e-mail ─────────────────────────────────────────────────────────────

class TestLogEmail:
    def test_registrar_sucesso(self, db):
        dados = InscricaoCreate(
            cpf="10203040506",
            nome="Log Test",
            email="log@test.com",
            instituicao="INPE",
            categoria=Categoria.PROFISSIONAL,
        )
        p = svc.criar_participante(db, dados)
        log = svc.registrar_log_email(
            db, p.id, TipoEmail.RECEBIMENTO, p.email, StatusEmail.ENVIADO
        )
        assert log.id is not None
        assert log.status == StatusEmail.ENVIADO
        assert log.erro is None

    def test_registrar_falha_com_erro(self, db):
        dados = InscricaoCreate(
            cpf="60504030201",
            nome="Falha Test",
            email="falha@test.com",
            instituicao="UFRJ",
            categoria=Categoria.PROFISSIONAL,
        )
        p = svc.criar_participante(db, dados)
        log = svc.registrar_log_email(
            db, p.id, TipoEmail.APROVACAO, p.email, StatusEmail.FALHA, "Connection refused"
        )
        assert log.status == StatusEmail.FALHA
        assert "refused" in log.erro


# ── Dashboard ─────────────────────────────────────────────────────────────────

class TestDashboard:
    def test_dashboard_vazio(self, db):
        stats = svc.get_dashboard_stats(db)
        assert stats["total_inscritos"] == 0
        assert all(v == 0 for v in stats.values())

    def test_dashboard_contagens(self, db):
        # Cria 2 participantes
        for i in range(2):
            svc.criar_participante(
                db,
                InscricaoCreate(
                    cpf=f"9900000000{i}",
                    nome=f"P{i}",
                    email=f"p{i}@d.com",
                    instituicao="ITA" if i == 0 else "USP",
                    matricula_ita="GE1" if i == 0 else None,
                    categoria=Categoria.GRADUACAO,
                ),
            )
        stats = svc.get_dashboard_stats(db)
        assert stats["total_inscritos"] == 2
        assert stats["total_ita"] == 1
        assert stats["total_externos"] == 1
        assert stats["pendentes"] == 2
