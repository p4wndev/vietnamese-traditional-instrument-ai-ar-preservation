"""
MongoDB client helper.

Usage in route handlers::

    from app.core.database import get_collection

    collection = get_collection("video_detection_results")
"""

import logging
from typing import Optional

from pymongo import MongoClient
from pymongo.collection import Collection

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: Optional[MongoClient] = None


def _get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(settings.MONGODB_URI)
    return _client


def get_collection(collection_name: str) -> Collection:
    client = _get_client()
    db = client[settings.MONGODB_DB_NAME]
    return db[collection_name]
