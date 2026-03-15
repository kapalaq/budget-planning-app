"""MongoDB connection setup."""

import logging

from pymongo import MongoClient
from pymongo.database import Database

logger = logging.getLogger(__name__)


def get_mongo_db(uri: str, db_name: str) -> Database:
    """Create a MongoClient and return the specified database."""
    client: MongoClient = MongoClient(uri)
    logger.info("Connected to MongoDB (%s)", db_name)
    return client[db_name]
