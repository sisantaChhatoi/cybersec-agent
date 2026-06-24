from functools import lru_cache

from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from shared.config import settings


@lru_cache
def _client() -> AsyncMongoClient:
    return AsyncMongoClient(settings.mongodb_uri)


def get_database() -> AsyncDatabase:
    return _client()[settings.mongodb_db]
