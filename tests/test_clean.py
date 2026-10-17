from etl.clean import classify_region, clean, extract_stipend, extract_technologies, normalize


def make_job(**overrides):
    """A raw posting shaped like Gupy's API response."""
    job = {
        "id": 1,
        "name": "Estágio em Dados",
        "description": "Requisitos: Python e SQL. Bolsa-auxílio: R$ 1.800,00",
        "careerPageName": "Empresa X",
        "careerPageLogo": None,
        "type": "vacancy_type_internship",
        "publishedDate": "2026-10-16T18:10:25.749Z",
        "applicationDeadline": "2026-12-05T00:00:00.000Z",
        "workplaceType": "hybrid",
        "city": "Barueri",
        "state": "São Paulo",
        "jobUrl": "https://example.gupy.io/job/1",
    }
    job.update(overrides)
    return job


def test_normalize_removes_accents_case_and_extra_spaces():
    assert normalize("  Carapicuíba   SP ") == "carapicuiba sp"
    assert normalize(None) == ""


def test_classify_region():
    assert classify_region("Cotia", "presencial", "") == "Cotia"
    assert classify_region("Carapicuiba", "hibrido", "") == "Carapicuíba"
    assert classify_region("Recife", "remoto", "") == "remoto"
    assert classify_region("São Paulo", "presencial", "escritorio em pinheiros") == "SP - zona oeste"
    assert classify_region("São Paulo", "presencial", "") == "SP - outras zonas"
    assert classify_region("Recife", "presencial", "") == "outra"


def test_extract_technologies():
    assert extract_technologies("python, sql e power bi") == ["Power BI", "Python", "SQL"]
    assert extract_technologies("javascript nao e java") == ["Java", "JavaScript"]


def test_extract_stipend():
    assert extract_stipend("bolsa de r$ 1.800,00 por mes") == 1800
    assert extract_stipend("vale-refeicao r$ 30,00") is None
    assert extract_stipend("sem bolsa informada") is None


def test_clean_filters_dedupes_and_normalizes():
    raw = [
        make_job(),
        make_job(),  # duplicate id
        make_job(id=2, name="Estágio Senior em Dados"),
        make_job(id=3, name="Estágio em Vendas"),
        make_job(id=4, type="vacancy_type_effective"),
        make_job(id=5, name="Estágio Desenvolvedor Front-end", workplaceType="remote"),
    ]
    df = clean(raw)

    assert sorted(df["gupy_id"]) == [1, 5]
    first = df[df["gupy_id"] == 1].iloc[0]
    assert first["modalidade"] == "hibrido"
    assert first["regiao"] == "Barueri"
    assert first["bolsa"] == 1800
    assert first["tecnologias"] == ["Python", "SQL"]
    assert df[df["gupy_id"] == 5].iloc[0]["regiao"] == "remoto"


def test_clean_empty_input():
    assert clean([]).empty
