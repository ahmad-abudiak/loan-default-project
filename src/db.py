"""Database connection helpers for the loan default project."""

from sqlalchemy import create_engine
from sqlalchemy.engine import URL


def get_engine(database="LoanDefault", fast_executemany=False):
    """Return a SQLAlchemy engine connected to the local SQL Server."""
    connection_url = URL.create(
        "mssql+pyodbc",
        host="localhost",
        database=database,
        query={
            "driver": "ODBC Driver 17 for SQL Server",
            "trusted_connection": "yes",
        },
    )
    return create_engine(connection_url, fast_executemany=fast_executemany)