"""Collects internship job postings from Gupy's public job-search API."""
import time

import requests

API_URL = "https://portal.gupy.io/api/job-search/jobs"
SEARCH_TERMS = [
    "dados", "desenvolvimento", "desenvolvedor", "software", "tecnologia", "TI",
    "programação", "sistemas", "python", "sql", "front-end", "back-end", "full stack",
    "BI", "analytics", "computação", "informática", "suporte", "inteligência artificial",
    "cloud", "devops", "web", "infraestrutura", "redes", "segurança da informação",
]
JOB_TYPE = "vacancy_type_internship"  # the API filters internships for us
PAGE_SIZE = 100
MAX_PAGES_PER_TERM = 5
PAUSE_SECONDS = 1.0  # be polite: at most one request per second


def fetch_term(term: str, session: requests.Session) -> list[dict]:
    """Returns every posting for one search term, page by page."""
    jobs = []
    for page in range(MAX_PAGES_PER_TERM):
        params = {"jobName": term, "type": JOB_TYPE, "limit": PAGE_SIZE, "offset": page * PAGE_SIZE}
        response = session.get(API_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()["data"]
        jobs.extend(data)
        if len(data) < PAGE_SIZE:
            break
        time.sleep(PAUSE_SECONDS)
    return jobs


def collect() -> list[dict]:
    """Runs all search terms and returns the raw postings (may contain duplicates)."""
    session = requests.Session()
    session.headers["User-Agent"] = "radar-estagios (student portfolio project)"
    raw = []
    for term in SEARCH_TERMS:
        jobs = fetch_term(term, session)
        print(f"{term!r}: {len(jobs)} postings")
        raw.extend(jobs)
        time.sleep(PAUSE_SECONDS)
    return raw
