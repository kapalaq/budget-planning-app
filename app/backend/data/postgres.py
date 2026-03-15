"""PostgreSQL connection setup."""

import logging

import psycopg2

logger = logging.getLogger(__name__)


def get_postgres_conn(dsn: str):
    """Create and return a psycopg2 connection with autocommit enabled."""
    conn = psycopg2.connect(dsn)
    conn.autocommit = True
    logger.info("Connected to PostgreSQL")
    return conn
