"""Loads the cleaned DataFrame into PostgreSQL (upsert: insert or update)."""
import pandas as pd
import psycopg

UPSERT_EMPRESA = """
    INSERT INTO empresas (nome, logo_url) VALUES (%s, %s)
    ON CONFLICT (nome) DO UPDATE SET logo_url = EXCLUDED.logo_url
    RETURNING id
"""

UPSERT_VAGA = """
    INSERT INTO vagas (gupy_id, empresa_id, titulo, cidade, estado, regiao, modalidade,
                       bolsa, tecnologias, url, publicada_em, prazo)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (gupy_id) DO UPDATE SET
        titulo = EXCLUDED.titulo, cidade = EXCLUDED.cidade, estado = EXCLUDED.estado,
        regiao = EXCLUDED.regiao, modalidade = EXCLUDED.modalidade, bolsa = EXCLUDED.bolsa,
        tecnologias = EXCLUDED.tecnologias, url = EXCLUDED.url, prazo = EXCLUDED.prazo,
        coletada_em = now()
"""


def none_if_nan(value):
    """pandas usa NaN/NaT para vazio; o banco precisa de None (NULL)."""
    return None if pd.isna(value) else value


def load(df: pd.DataFrame, database_url: str) -> int:
    """Grava empresas e vagas numa única transação. Retorna quantas vagas foram gravadas."""
    if df.empty:
        return 0
    with psycopg.connect(database_url) as conn, conn.cursor() as cur:
        empresa_ids = {}
        empresas = df[["empresa", "logo_url"]].drop_duplicates("empresa")
        for nome, logo in empresas.itertuples(index=False):
            cur.execute(UPSERT_EMPRESA, (nome, none_if_nan(logo)))
            empresa_ids[nome] = cur.fetchone()[0]

        rows = [
            (
                int(row.gupy_id), empresa_ids[row.empresa], row.titulo,
                none_if_nan(row.cidade), none_if_nan(row.estado), row.regiao, row.modalidade,
                none_if_nan(row.bolsa), list(row.tecnologias), row.url,
                none_if_nan(row.publicada_em), none_if_nan(row.prazo),
            )
            for row in df.itertuples(index=False)
        ]
        cur.executemany(UPSERT_VAGA, rows)
    return len(rows)
