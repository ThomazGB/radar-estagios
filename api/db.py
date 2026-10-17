"""Database connection pool shared by every request."""
import os

from dotenv import load_dotenv
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

load_dotenv()

# open=False: the pool only connects when the app starts (see main.lifespan)
pool = ConnectionPool(
    os.environ["DATABASE_URL"],
    min_size=1,
    max_size=5,
    kwargs={"row_factory": dict_row},  # rows come back as dicts -> easy to return as JSON
    open=False,
)


def get_conn():
    """FastAPI dependency: borrows a connection and gives it back after the request."""
    with pool.connection() as conn:
        yield conn
