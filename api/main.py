"""Radar de Estágios API.  Run locally: uvicorn api.main:app --reload"""
import os
from contextlib import asynccontextmanager
from typing import Literal

import psycopg
from fastapi import Depends, FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from api.db import get_conn, pool

Status = Literal["interessado", "candidatei", "entrevista", "resultado"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool.open()
    yield
    pool.close()


app = FastAPI(title="Radar de Estágios API", lifespan=lifespan)

# CORS is configured HERE, on the back end: the browser asks the API which sites may call it
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(","),
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type"],
)


class CandidaturaIn(BaseModel):
    vaga_id: int
    status: Status = "interessado"


class CandidaturaPatch(BaseModel):
    status: Status | None = None
    notas: str | None = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/vagas")
def list_vagas(
    regiao: str | None = None,
    modalidade: str | None = None,
    tecnologia: str | None = None,
    busca: str | None = Query(None, description="texto no título ou na empresa"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    conn: psycopg.Connection = Depends(get_conn),
):
    # Every value goes as a %s parameter, never glued into the string -> no SQL injection
    where, params = [], []
    if regiao:
        where.append("v.regiao = %s")
        params.append(regiao)
    if modalidade:
        where.append("v.modalidade = %s")
        params.append(modalidade)
    if tecnologia:
        where.append("%s = ANY(v.tecnologias)")
        params.append(tecnologia)
    if busca:
        where.append("(v.titulo ILIKE %s OR e.nome ILIKE %s)")
        params += [f"%{busca}%", f"%{busca}%"]
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    rows = conn.execute(
        f"""
        SELECT v.id, v.titulo, e.nome AS empresa, e.logo_url, v.cidade, v.estado, v.regiao,
               v.modalidade, v.bolsa, v.tecnologias, v.url, v.publicada_em, v.prazo,
               c.id AS candidatura_id, c.status AS candidatura_status,
               COUNT(*) OVER () AS total
        FROM vagas v
        JOIN empresas e ON e.id = v.empresa_id
        LEFT JOIN candidaturas c ON c.vaga_id = v.id
        {where_sql}
        ORDER BY v.publicada_em DESC NULLS LAST
        LIMIT %s OFFSET %s
        """,
        [*params, limit, offset],
    ).fetchall()
    total = rows[0]["total"] if rows else 0
    for row in rows:
        del row["total"]
    return {"total": total, "itens": rows}


@app.get("/filtros")
def list_filters(conn: psycopg.Connection = Depends(get_conn)):
    """Options for the dropdowns in the dashboard."""
    regioes = conn.execute(
        "SELECT regiao, COUNT(*) AS total FROM vagas GROUP BY regiao ORDER BY total DESC"
    ).fetchall()
    tecnologias = conn.execute(
        """
        SELECT tec AS tecnologia, COUNT(*) AS total
        FROM vagas, unnest(tecnologias) AS tec
        GROUP BY tec ORDER BY total DESC
        """
    ).fetchall()
    return {"regioes": regioes, "tecnologias": tecnologias}


@app.get("/candidaturas")
def list_candidaturas(conn: psycopg.Connection = Depends(get_conn)):
    return conn.execute(
        """
        SELECT c.id, c.vaga_id, c.status, c.notas, c.atualizada_em,
               v.titulo, e.nome AS empresa, v.regiao, v.url
        FROM candidaturas c
        JOIN vagas v ON v.id = c.vaga_id
        JOIN empresas e ON e.id = v.empresa_id
        ORDER BY c.atualizada_em DESC
        """
    ).fetchall()


@app.post("/candidaturas", status_code=201)
def create_candidatura(body: CandidaturaIn, conn: psycopg.Connection = Depends(get_conn)):
    if conn.execute("SELECT 1 FROM vagas WHERE id = %s", [body.vaga_id]).fetchone() is None:
        raise HTTPException(404, "Vaga não encontrada")
    try:
        return conn.execute(
            "INSERT INTO candidaturas (vaga_id, status) VALUES (%s, %s) RETURNING *",
            [body.vaga_id, body.status],
        ).fetchone()
    except psycopg.errors.UniqueViolation:
        raise HTTPException(409, "Essa vaga já está no seu kanban")


@app.patch("/candidaturas/{candidatura_id}")
def update_candidatura(
    candidatura_id: int, body: CandidaturaPatch, conn: psycopg.Connection = Depends(get_conn)
):
    changes = body.model_dump(exclude_none=True)  # only the fields that were sent
    if not changes:
        raise HTTPException(422, "Envie status e/ou notas")
    # Column names come from our own model (never from the user), values go as parameters
    set_sql = ", ".join(f"{column} = %s" for column in changes)
    row = conn.execute(
        f"UPDATE candidaturas SET {set_sql}, atualizada_em = now() WHERE id = %s RETURNING *",
        [*changes.values(), candidatura_id],
    ).fetchone()
    if row is None:
        raise HTTPException(404, "Candidatura não encontrada")
    return row


@app.delete("/candidaturas/{candidatura_id}", status_code=204)
def delete_candidatura(candidatura_id: int, conn: psycopg.Connection = Depends(get_conn)):
    deleted = conn.execute("DELETE FROM candidaturas WHERE id = %s", [candidatura_id]).rowcount
    if not deleted:
        raise HTTPException(404, "Candidatura não encontrada")
    return Response(status_code=204)


@app.get("/estatisticas")
def statistics(conn: psycopg.Connection = Depends(get_conn)):
    def count_by(sql):
        return conn.execute(sql).fetchall()

    return {
        "total_vagas": conn.execute("SELECT COUNT(*) AS n FROM vagas").fetchone()["n"],
        "por_regiao": count_by(
            "SELECT regiao AS nome, COUNT(*) AS total FROM vagas GROUP BY regiao ORDER BY total DESC"
        ),
        "por_modalidade": count_by(
            "SELECT modalidade AS nome, COUNT(*) AS total FROM vagas GROUP BY modalidade ORDER BY total DESC"
        ),
        "top_tecnologias": count_by(
            """
            SELECT tec AS nome, COUNT(*) AS total FROM vagas, unnest(tecnologias) AS tec
            GROUP BY tec ORDER BY total DESC LIMIT 10
            """
        ),
        "bolsa_media_por_regiao": count_by(
            """
            SELECT regiao AS nome, ROUND(AVG(bolsa)) AS total FROM vagas
            WHERE bolsa IS NOT NULL GROUP BY regiao HAVING COUNT(*) >= 2 ORDER BY total DESC
            """
        ),
        "candidaturas_por_status": count_by(
            "SELECT status AS nome, COUNT(*) AS total FROM candidaturas GROUP BY status"
        ),
    }
