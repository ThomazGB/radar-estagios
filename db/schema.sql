-- Radar de Estágios — database schema (PostgreSQL)

CREATE TABLE IF NOT EXISTS empresas (
    id        SERIAL PRIMARY KEY,
    nome      TEXT NOT NULL UNIQUE,
    logo_url  TEXT
);

CREATE TABLE IF NOT EXISTS vagas (
    id             SERIAL PRIMARY KEY,
    gupy_id        BIGINT NOT NULL UNIQUE,          -- id na fonte, evita duplicar
    empresa_id     INTEGER NOT NULL REFERENCES empresas(id),
    titulo         TEXT NOT NULL,
    cidade         TEXT,
    estado         TEXT,
    regiao         TEXT NOT NULL,                   -- remoto, Cotia, Barueri, ..., outra
    modalidade     TEXT NOT NULL CHECK (modalidade IN ('remoto', 'hibrido', 'presencial')),
    bolsa          NUMERIC(10, 2),                  -- NULL quando a vaga não informa
    tecnologias    TEXT[] NOT NULL DEFAULT '{}',
    url            TEXT NOT NULL,
    publicada_em   TIMESTAMPTZ,
    prazo          DATE,
    coletada_em    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS candidaturas (
    id             SERIAL PRIMARY KEY,
    vaga_id        INTEGER NOT NULL UNIQUE REFERENCES vagas(id) ON DELETE CASCADE,
    status         TEXT NOT NULL DEFAULT 'interessado'
                   CHECK (status IN ('interessado', 'candidatei', 'entrevista', 'resultado')),
    notas          TEXT NOT NULL DEFAULT '',
    criada_em      TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizada_em  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Índices para os filtros mais usados no painel
CREATE INDEX IF NOT EXISTS idx_vagas_regiao      ON vagas (regiao);
CREATE INDEX IF NOT EXISTS idx_vagas_modalidade  ON vagas (modalidade);
CREATE INDEX IF NOT EXISTS idx_vagas_tecnologias ON vagas USING GIN (tecnologias);
CREATE INDEX IF NOT EXISTS idx_vagas_publicada   ON vagas (publicada_em DESC);
