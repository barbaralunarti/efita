# backend/tests/test_inscricao.py
"""Testes para as rotas públicas de inscrição."""
import pytest
from unittest.mock import AsyncMock, patch


PAYLOAD_EXTERNO = {
    "cpf": "05623895719",
    "nome": "João da Silva",
    "email": "joao@exemplo.com",
    "instituicao": "USP",
    "categoria": "graduacao",
    "poster": None,
}

PAYLOAD_ITA_GRAD = {
    "cpf": "28287415594",
    "nome": "Maria ITA",
    "email": "maria@ita.br",
    "instituicao": "ITA",
    "matricula_ita": "GE123",
    "categoria": "graduacao",
}

PAYLOAD_ITA_PROF = {
    "cpf": "83261054654",
    "nome": "Prof ITA",
    "email": "prof@ita.br",
    "instituicao": "ITA",
    "categoria": "professor",
}


# ── POST /api/inscricao ────────────────────────────────────────────────────────

class TestCriarInscricao:
    def test_inscricao_externa_sucesso(self, client):
        """Cenário de sucesso: inscrição de participante externo."""
        with patch("app.services.email.email_service.enqueue", new_callable=AsyncMock):
            resp = client.post("/api/inscricao", json=PAYLOAD_EXTERNO)
        assert resp.status_code == 201
        data = resp.json()
        assert data["nome"] == "João da Silva"
        assert data["is_ita"] is False
        assert data["status_inscricao"] == "pendente"
        assert data["status_pagamento"] == "pendente"
        assert data["protocolo"].startswith("EFITA-2025-")
        assert "cpf_mascarado" in data
        # CPF não deve aparecer em claro
        assert "05623895719" not in resp.text

    def test_inscricao_ita_graduacao_sucesso(self, client):
        """Aluno ITA de graduação com matrícula → sucesso; pagamento NAO_APLICAVEL."""
        with patch("app.services.email.email_service.enqueue", new_callable=AsyncMock):
            resp = client.post("/api/inscricao", json=PAYLOAD_ITA_GRAD)
        assert resp.status_code == 201
        data = resp.json()
        assert data["is_ita"] is True
        assert data["status_pagamento"] == "nao_aplicavel"

    def test_inscricao_ita_professor_sem_matricula(self, client):
        """Professor do ITA sem matrícula → sucesso (matrícula não obrigatória)."""
        with patch("app.services.email.email_service.enqueue", new_callable=AsyncMock):
            resp = client.post("/api/inscricao", json=PAYLOAD_ITA_PROF)
        assert resp.status_code == 201
        assert resp.json()["is_ita"] is True

    def test_inscricao_ita_graduacao_sem_matricula_falha(self, client):
        """Aluno ITA de graduação sem matrícula → deve retornar 422."""
        payload = PAYLOAD_ITA_GRAD.copy()
        del payload["matricula_ita"]
        resp = client.post("/api/inscricao", json=payload)
        assert resp.status_code == 422

    def test_cpf_invalido(self, client):
        """CPF com menos de 11 dígitos → 422."""
        payload = {**PAYLOAD_EXTERNO, "cpf": "1234"}
        resp = client.post("/api/inscricao", json=payload)
        assert resp.status_code == 422

    def test_email_invalido(self, client):
        """E-mail mal formatado → 422."""
        payload = {**PAYLOAD_EXTERNO, "email": "nao-e-um-email"}
        resp = client.post("/api/inscricao", json=payload)
        assert resp.status_code == 422

    def test_cpf_duplicado(self, client):
        """Tentativa de registrar o mesmo CPF duas vezes → 409."""
        with patch("app.services.email.email_service.enqueue", new_callable=AsyncMock):
            client.post("/api/inscricao", json=PAYLOAD_EXTERNO)
            resp = client.post("/api/inscricao", json=PAYLOAD_EXTERNO)
        assert resp.status_code == 409

    def test_email_duplicado(self, client):
        """Mesmo e-mail, CPF diferente → 409."""
        with patch("app.services.email.email_service.enqueue", new_callable=AsyncMock):
            client.post("/api/inscricao", json=PAYLOAD_EXTERNO)
            payload2 = {**PAYLOAD_EXTERNO, "cpf": "58829757942"}
            resp = client.post("/api/inscricao", json=payload2)
        assert resp.status_code == 409

    def test_inscricao_com_poster(self, client):
        """Inscrição com pôster → tem_poster=True."""
        payload = {
            **PAYLOAD_EXTERNO,
            "poster": {
                "titulo": "Dinâmica de Fluidos",
                "resumo": "Um estudo avançado sobre...",
                "palavras_chave": "fluidos, dinâmica",
            },
        }
        with patch("app.services.email.email_service.enqueue", new_callable=AsyncMock):
            resp = client.post("/api/inscricao", json=payload)
        assert resp.status_code == 201
        assert resp.json()["tem_poster"] is True

    def test_email_enfileirado_apos_inscricao(self, client):
        """E-mail de recebimento deve ser enfileirado após inscrição bem-sucedida."""
        with patch("app.services.email.email_service.enqueue", new_callable=AsyncMock) as mock_enqueue:
            resp = client.post("/api/inscricao", json=PAYLOAD_EXTERNO)
        assert resp.status_code == 201
        mock_enqueue.assert_called_once()
        call_kwargs = mock_enqueue.call_args[0]
        assert call_kwargs[0] == PAYLOAD_EXTERNO["email"]  # destinatário


# ── GET /api/inscricao/{cpf} ──────────────────────────────────────────────────

class TestConsultarInscricao:
    def test_consultar_existente(self, client):
        """Consulta retorna dados da inscrição pelo CPF."""
        with patch("app.services.email.email_service.enqueue", new_callable=AsyncMock):
            client.post("/api/inscricao", json=PAYLOAD_EXTERNO)

        resp = client.get(f"/api/inscricao/{PAYLOAD_EXTERNO['cpf']}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["nome"] == PAYLOAD_EXTERNO["nome"]
        # CPF mascarado
        assert data["cpf_mascarado"] != PAYLOAD_EXTERNO["cpf"]

    def test_consultar_inexistente(self, client):
        """CPF não cadastrado → 404."""
        resp = client.get("/api/inscricao/31423225740")
        assert resp.status_code == 404

    def test_consultar_com_formatacao_cpf(self, client):
        """CPF com formatação (pontos e hífen) deve funcionar."""
        with patch("app.services.email.email_service.enqueue", new_callable=AsyncMock):
            client.post("/api/inscricao", json=PAYLOAD_EXTERNO)
        resp = client.get("/api/inscricao/056.238.957-19")
        assert resp.status_code == 200
