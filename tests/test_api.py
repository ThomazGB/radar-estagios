"""API tests. They need a PostgreSQL with schema.sql applied (DATABASE_URL)."""
import os

import psycopg
import pytest
from dotenv import load_dotenv

load_dotenv()
if not os.getenv("DATABASE_URL"):
    pytest.skip("DATABASE_URL not set", allow_module_level=True)

from fastapi.testclient import TestClient  # noqa: E402

from api.main import app  # noqa: E402

TEST_GUPY_ID = -1  # negative id: never collides with real postings


@pytest.fixture(scope="module")  # one app start/stop for all tests (the pool can't reopen)
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def vaga_id():
    """Creates one posting just for the test and removes it afterwards."""
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        empresa_id = conn.execute(
            "INSERT INTO empresas (nome) VALUES ('Empresa Teste') "
            "ON CONFLICT (nome) DO UPDATE SET nome = EXCLUDED.nome RETURNING id"
        ).fetchone()[0]
        new_id = conn.execute(
            """
            INSERT INTO vagas (gupy_id, empresa_id, titulo, cidade, regiao, modalidade,
                               tecnologias, url)
            VALUES (%s, %s, 'Estágio Teste em Dados', 'Cotia', 'Cotia', 'hibrido',
                    '{Python,SQL}', 'https://example.com')
            RETURNING id
            """,
            [TEST_GUPY_ID, empresa_id],
        ).fetchone()[0]
    yield new_id
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        conn.execute("DELETE FROM vagas WHERE gupy_id = %s", [TEST_GUPY_ID])
        conn.execute("DELETE FROM empresas WHERE nome = 'Empresa Teste'")


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_filter_vagas(client, vaga_id):
    body = client.get("/vagas", params={"regiao": "Cotia", "tecnologia": "SQL"}).json()
    assert vaga_id in [v["id"] for v in body["itens"]]

    body = client.get("/vagas", params={"busca": "Teste em Dados", "modalidade": "remoto"}).json()
    assert vaga_id not in [v["id"] for v in body["itens"]]


def test_sql_injection_is_just_text(client, vaga_id):
    response = client.get("/vagas", params={"busca": "'; DROP TABLE vagas; --"})
    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_candidatura_lifecycle(client, vaga_id):
    created = client.post("/candidaturas", json={"vaga_id": vaga_id})
    assert created.status_code == 201
    cand_id = created.json()["id"]
    assert created.json()["status"] == "interessado"

    assert client.post("/candidaturas", json={"vaga_id": vaga_id}).status_code == 409

    patched = client.patch(f"/candidaturas/{cand_id}", json={"status": "entrevista"})
    assert patched.status_code == 200
    assert patched.json()["status"] == "entrevista"

    assert client.patch(f"/candidaturas/{cand_id}", json={"status": "aprovado"}).status_code == 422
    assert client.delete(f"/candidaturas/{cand_id}").status_code == 204
    assert client.delete(f"/candidaturas/{cand_id}").status_code == 404


def test_candidatura_for_missing_vaga(client):
    assert client.post("/candidaturas", json={"vaga_id": 999999999}).status_code == 404


def test_statistics(client, vaga_id):
    body = client.get("/estatisticas").json()
    assert body["total_vagas"] >= 1
    assert any(item["nome"] == "Cotia" for item in body["por_regiao"])
