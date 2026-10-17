"""Cleans raw Gupy postings with pandas: normalizes, filters and deduplicates."""
import html
import re
import unicodedata

import pandas as pd

TARGET_CITIES = [
    "Cotia", "Barueri", "Osasco", "Santana de Parnaíba", "Itapevi",
    "Carapicuíba", "Taboão da Serra", "Jandira", "Vargem Grande Paulista",
]
# Bairros da zona oeste de SP (a fonte só informa "São Paulo" como cidade)
ZONA_OESTE = [
    "zona oeste", "pinheiros", "butanta", "lapa", "vila leopoldina", "barra funda",
    "perdizes", "vila madalena", "jaguare", "alto de pinheiros", "faria lima",
]
MODALIDADES = {"remote": "remoto", "hybrid": "hibrido", "on-site": "presencial"}

# Padrão procurado no texto -> nome padronizado da tecnologia
TECNOLOGIAS = {
    r"python": "Python", r"\bsql\b": "SQL", r"power ?bi": "Power BI",
    r"excel": "Excel", r"javascript|\bjs\b": "JavaScript", r"typescript": "TypeScript",
    r"react": "React", r"node(\.js)?\b": "Node.js", r"\bjava\b": "Java",
    r"c#|\.net\b": "C#/.NET", r"\bphp\b": "PHP", r"\bgit\b": "Git",
    r"docker": "Docker", r"\baws\b": "AWS", r"azure": "Azure",
    r"tableau": "Tableau", r"pandas": "pandas", r"postgres": "PostgreSQL",
    r"html": "HTML", r"\bcss\b": "CSS", r"\bapis?\b": "APIs", r"linux": "Linux",
}

# O título precisa ter um destes termos para contar como vaga de tecnologia
TECH_TITLE = (
    r"dados|\bdata\b|\bti\b|tecnologia|software|sistemas|programacao|programador|"
    r"desenvolvedor|desenvolvimento (?:de )?(?:software|sistemas|web|aplica|front|back)|"
    r"\bdev\b|\bbi\b|analytics|front.?end|back.?end|full.?stack|devops|cloud|"
    r"infraestrutura de ti|redes|suporte (?:tecnico|de ti|ti)|help ?desk|computacao|"
    r"informatica|inteligencia artificial|\bia\b|machine learning|seguranca da informacao|"
    r"ciberseguranca|python|\bsql\b|power bi|\bqa\b|testes de software|\bweb\b"
)
# Não é estágio de verdade ou não serve para o perfil
EXCLUDE_TITLE = (
    r"senior|pleno|junior|\bclt\b|trainee|aprendiz|producao|engenharia civil|"
    r"redes sociais|vendas|comercial|marketing"
)


def strip_accents(text: str) -> str:
    """'Carapicuíba' -> 'Carapicuiba' (para comparar sem se preocupar com acento)."""
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def normalize(text) -> str:
    """Minúsculas, sem acento e sem espaços extras. Valor vazio vira ''."""
    if not isinstance(text, str):
        return ""
    return " ".join(strip_accents(text).lower().split())


def classify_region(cidade, modalidade: str, texto: str) -> str:
    """Decide em qual região do filtro a vaga entra."""
    if modalidade == "remoto":
        return "remoto"
    cidade_norm = normalize(cidade)
    for target in TARGET_CITIES:
        if cidade_norm == normalize(target):
            return target
    if cidade_norm == "sao paulo":
        if any(bairro in texto for bairro in ZONA_OESTE):
            return "SP - zona oeste"
        return "SP - outras zonas"
    return "outra"


def extract_technologies(texto: str) -> list[str]:
    """Procura cada tecnologia conhecida no texto (já normalizado)."""
    return sorted({name for pattern, name in TECNOLOGIAS.items() if re.search(pattern, texto)})


def extract_stipend(texto: str):
    """Pega o primeiro valor tipo 'R$ 1.800,00' que pareça bolsa; None se não achar."""
    for match in re.finditer(r"r\$\s*(\d{1,2}\.?\d{3})(,\d{2})?", texto):
        value = float(match.group(1).replace(".", ""))
        if 500 <= value <= 10000:
            return value
    return None


def clean(raw: list[dict]) -> pd.DataFrame:
    """Transforma a lista crua da API em um DataFrame pronto para o banco."""
    df = pd.DataFrame(raw)
    if df.empty:
        return df

    df = df[df["type"] == "vacancy_type_internship"]
    df = df.drop_duplicates(subset="id").copy()

    df["titulo"] = df["name"].str.strip()
    titulo_norm = df["titulo"].map(normalize)
    keep = titulo_norm.str.contains(TECH_TITLE) & ~titulo_norm.str.contains(EXCLUDE_TITLE)
    df = df[keep].copy()

    descricao = df["description"].fillna("").map(html.unescape)
    texto = (df["titulo"] + " " + descricao).map(normalize)

    df["empresa"] = df["careerPageName"].str.strip()
    df["cidade"] = df["city"].fillna("").str.strip().str.title().replace("", None)
    df["estado"] = df["state"].fillna("").str.strip().replace("", None)
    df["modalidade"] = df["workplaceType"].map(MODALIDADES).fillna("presencial")
    df["regiao"] = [
        classify_region(c, m, t) for c, m, t in zip(df["cidade"], df["modalidade"], texto)
    ]
    df["tecnologias"] = texto.map(extract_technologies)
    df["bolsa"] = texto.map(extract_stipend)
    df["publicada_em"] = pd.to_datetime(df["publishedDate"], errors="coerce", utc=True)
    df["prazo"] = pd.to_datetime(df["applicationDeadline"], errors="coerce", utc=True).dt.date

    df = df.rename(columns={"id": "gupy_id", "careerPageLogo": "logo_url", "jobUrl": "url"})
    columns = [
        "gupy_id", "empresa", "logo_url", "titulo", "cidade", "estado", "regiao",
        "modalidade", "bolsa", "tecnologias", "url", "publicada_em", "prazo",
    ]
    return df[columns].reset_index(drop=True)
