# backend/tests/test_admin.py
"""Testes para as rotas protegidas do admin."""
import pytest
from unittest.mock import AsyncMock, patch

from app.auth import hash_password
from app.models import Admin, Participante, StatusInscricao, StatusPagamento


PARTICIPANTE_EXTERNO = {
    "cpf": "12345678901",
    "nome": "Externo Teste",
    "email": "externo@test.com",
    "instituicao": "USP",
    "categoria": "profissional",
}

PARTICIPANTE_ITA = {
    "cpf": "11122233344",
    "nome": "ITA Teste",
    "email": "ita@test.com",
    "instituicao": "ITA",
    "categoria": "professor",
}

PARTICIPANTE_COM_POSTER = {
    "cpf": "99988877766",
    "nome": "Com Poster",
    "email": "poster@test.com",
    "instituicao": "USP",
    "categoria": "pos_graduacao",
    "poster": {
        "titulo": "Meu Poster",
        "resumo": "Este é um resumo muito legal.",
        "palavras_chave": "fisica, teste"
    }
}


def criar_inscricao(client, payload):
    with patch("app.services.email.email_service.enqueue", new_callable=AsyncMock):
        r = client.post("/api/inscricao", json=payload)
    assert r.status_code == 201
    return r.json()


# ── Autenticação ──────────────────────────────────────────────────────────────

class TestLogin:
    def test_login_sucesso(self, client, db):
        admin = Admin(username="admin", password_hash=hash_password("senha123"))
        db.add(admin)
        db.commit()
        resp = client.post("/api/admin/login", data={"username": "admin", "password": "senha123"})
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_login_senha_errada(self, client, db):
        admin = Admin(username="admin", password_hash=hash_password("correta"))
        db.add(admin)
        db.commit()
        resp = client.post("/api/admin/login", data={"username": "admin", "password": "errada"})
        assert resp.status_code == 401

    def test_login_usuario_inexistente(self, client):
        resp = client.post("/api/admin/login", data={"username": "naoexiste", "password": "qualquer"})
        assert resp.status_code == 401

    def test_rota_sem_token_retorna_401(self, client):
        resp = client.get("/api/admin/participantes")
        assert resp.status_code == 401


# ── Participantes ─────────────────────────────────────────────────────────────

class TestParticipantes:
    def test_listar_vazio(self, client, auth_headers):
        resp = client.get("/api/admin/participantes", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_listar_com_participantes(self, client, auth_headers):
        criar_inscricao(client, PARTICIPANTE_EXTERNO)
        resp = client.get("/api/admin/participantes", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_filtrar_por_status(self, client, auth_headers):
        criar_inscricao(client, PARTICIPANTE_EXTERNO)
        resp = client.get(
            "/api/admin/participantes?status_inscricao=pendente", headers=auth_headers
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

        resp2 = client.get(
            "/api/admin/participantes?status_inscricao=aprovado", headers=auth_headers
        )
        assert resp2.json() == []

    def test_filtrar_por_is_ita(self, client, auth_headers):
        criar_inscricao(client, PARTICIPANTE_EXTERNO)
        criar_inscricao(client, PARTICIPANTE_ITA)
        resp = client.get(
            "/api/admin/participantes?is_ita=true", headers=auth_headers
        )
        assert len(resp.json()) == 1
        assert resp.json()[0]["is_ita"] is True

    def test_buscar_por_nome(self, client, auth_headers):
        criar_inscricao(client, PARTICIPANTE_EXTERNO)
        resp = client.get(
            "/api/admin/participantes?busca=Externo", headers=auth_headers
        )
        assert len(resp.json()) == 1

    def test_detalhe_existente(self, client, auth_headers):
        data = criar_inscricao(client, PARTICIPANTE_EXTERNO)
        resp = client.get(f"/api/admin/participantes/{data['id']}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["cpf"] == PARTICIPANTE_EXTERNO["cpf"]

    def test_detalhe_inexistente(self, client, auth_headers):
        resp = client.get("/api/admin/participantes/9999", headers=auth_headers)
        assert resp.status_code == 404


# ── Atualização de Status ─────────────────────────────────────────────────────

class TestStatusUpdate:
    def test_aprovar_participante_externo(self, client, auth_headers):
        data = criar_inscricao(client, PARTICIPANTE_EXTERNO)
        resp = client.patch(
            f"/api/admin/participantes/{data['id']}/status",
            json={"status_inscricao": "aprovado"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        updated = resp.json()
        assert updated["status_inscricao"] == "aprovado"
        assert updated["status_pagamento"] == "pendente"

    def test_aprovar_participante_ita(self, client, auth_headers):
        data = criar_inscricao(client, PARTICIPANTE_ITA)
        resp = client.patch(
            f"/api/admin/participantes/{data['id']}/status",
            json={"status_inscricao": "aprovado"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        updated = resp.json()
        assert updated["status_inscricao"] == "aprovado"
        assert updated["status_pagamento"] == "nao_aplicavel"

    def test_recusar_participante(self, client, auth_headers):
        data = criar_inscricao(client, PARTICIPANTE_EXTERNO)
        resp = client.patch(
            f"/api/admin/participantes/{data['id']}/status",
            json={"status_inscricao": "recusado"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status_inscricao"] == "recusado"

    def test_atualizar_pagamento(self, client, auth_headers):
        data = criar_inscricao(client, PARTICIPANTE_EXTERNO)
        # Primeiro aprova
        client.patch(
            f"/api/admin/participantes/{data['id']}/status",
            json={"status_inscricao": "aprovado"},
            headers=auth_headers,
        )
        # Depois confirma pagamento
        resp = client.patch(
            f"/api/admin/participantes/{data['id']}/pagamento",
            json={"status_pagamento": "pago"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status_pagamento"] == "pago"


# ── Dashboard ─────────────────────────────────────────────────────────────────

class TestDashboard:
    def test_dashboard_vazio(self, client, auth_headers):
        resp = client.get("/api/admin/dashboard", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_inscritos"] == 0
        assert data["pendentes"] == 0

    def test_dashboard_com_dados(self, client, auth_headers):
        criar_inscricao(client, PARTICIPANTE_EXTERNO)
        criar_inscricao(client, PARTICIPANTE_ITA)
        resp = client.get("/api/admin/dashboard", headers=auth_headers)
        data = resp.json()
        assert data["total_inscritos"] == 2
        assert data["pendentes"] == 2
        assert data["total_ita"] == 1
        assert data["total_externos"] == 1


# ── Emails ────────────────────────────────────────────────────────────────────

class TestEmails:
    def test_disparar_lote_sem_aprovados(self, client, auth_headers):
        criar_inscricao(client, PARTICIPANTE_EXTERNO)
        with patch("app.services.email.email_service.enqueue", new_callable=AsyncMock):
            resp = client.post("/api/admin/emails/disparar-lote", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["enfileirados"] == 0

    def test_disparar_lote_com_aprovados(self, client, auth_headers):
        data = criar_inscricao(client, PARTICIPANTE_EXTERNO)
        client.patch(
            f"/api/admin/participantes/{data['id']}/status",
            json={"status_inscricao": "aprovado"},
            headers=auth_headers,
        )
        with patch("app.services.email.email_service.enqueue", new_callable=AsyncMock) as mock_enqueue:
            resp = client.post("/api/admin/emails/disparar-lote", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["enfileirados"] == 1
        mock_enqueue.assert_called_once()

    def test_reenviar_nao_aprovado(self, client, auth_headers):
        data = criar_inscricao(client, PARTICIPANTE_EXTERNO)
        resp = client.post(
            f"/api/admin/emails/reenviar/{data['id']}", headers=auth_headers
        )
        assert resp.status_code == 404

    def test_reenviar_aprovado(self, client, auth_headers):
        data = criar_inscricao(client, PARTICIPANTE_EXTERNO)
        client.patch(
            f"/api/admin/participantes/{data['id']}/status",
            json={"status_inscricao": "aprovado"},
            headers=auth_headers,
        )
        with patch("app.services.email.email_service.enqueue", new_callable=AsyncMock):
            resp = client.post(
                f"/api/admin/emails/reenviar/{data['id']}", headers=auth_headers
            )
        assert resp.status_code == 200

    def test_log_emails(self, client, auth_headers):
        resp = client.get("/api/admin/emails/log", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


# ── Exportação CSV ────────────────────────────────────────────────────────────

class TestExportCSV:
    def test_export_csv_vazio(self, client, auth_headers):
        resp = client.get("/api/admin/export/csv", headers=auth_headers)
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]

    def test_export_csv_com_dados(self, client, auth_headers):
        criar_inscricao(client, PARTICIPANTE_EXTERNO)
        resp = client.get("/api/admin/export/csv", headers=auth_headers)
        assert resp.status_code == 200
        content = resp.text
        assert "EFITA-2025-" in content
        assert PARTICIPANTE_EXTERNO["nome"] in content


# ── Pôsteres ──────────────────────────────────────────────────────────────────

class TestPosters:
    def test_listar_posters(self, client, auth_headers):
        criar_inscricao(client, PARTICIPANTE_COM_POSTER)
        resp = client.get("/api/admin/posters", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["titulo"] == "Meu Poster"
        assert data[0]["status"] == "pendente"

    def test_atualizar_status_poster(self, client, auth_headers):
        criar_inscricao(client, PARTICIPANTE_COM_POSTER)
        resp = client.get("/api/admin/posters", headers=auth_headers)
        poster_id = resp.json()[0]["id"]
        
        resp_patch = client.patch(
            f"/api/admin/posters/{poster_id}/status",
            json={"status": "aprovado"},
            headers=auth_headers
        )
        assert resp_patch.status_code == 200
        assert resp_patch.json()["status"] == "aprovado"
        
        # Verifica na listagem novamente
        resp_get = client.get("/api/admin/posters", headers=auth_headers)
        assert resp_get.json()[0]["status"] == "aprovado"
