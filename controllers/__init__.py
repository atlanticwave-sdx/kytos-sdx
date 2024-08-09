"""SdxController."""

# pylint: disable=unnecessary-lambda,invalid-name
import os
from datetime import datetime
from typing import Dict, Optional

from pymongo.collection import ReturnDocument
from pymongo.errors import AutoReconnect
from tenacity import retry_if_exception_type, stop_after_attempt, wait_random

from kytos.core.db import Mongo
from kytos.core.retry import before_sleep, for_all_methods, retries


@for_all_methods(
    retries,
    stop=stop_after_attempt(
        int(os.environ.get("MONGO_AUTO_RETRY_STOP_AFTER_ATTEMPT", "3"))
    ),
    wait=wait_random(
        min=int(os.environ.get("MONGO_AUTO_RETRY_WAIT_RANDOM_MIN", "1")),
        max=int(os.environ.get("MONGO_AUTO_RETRY_WAIT_RANDOM_MAX", "1")),
    ),
    before_sleep=before_sleep,
    retry=retry_if_exception_type((AutoReconnect,)),
)
class MongoController:
    """Mongo Controller"""

    def __init__(self, get_mongo=lambda: Mongo()) -> None:
        self.mongo = get_mongo()
        self.db_client = self.mongo.client
        self.db = self.db_client[self.mongo.db_name]

    def get_topology(self) -> Dict:
        """Get latest SDX Topology."""
        return self.db.sdx_info.find_one({"_id": "topology"}) or {}

    def upsert_topology(self, sdx_topology: Dict) -> Optional[Dict]:
        """Update or insert an EVC"""
        utc_now = datetime.utcnow()
        sdx_topology["updated_at"] = utc_now
        sdx_topology.pop("inserted_at", None)
        updated = self.db.sdx_info.find_one_and_update(
            {"_id": "topology"},
            {
                "$set": sdx_topology,
                "$setOnInsert": {"inserted_at": utc_now},
            },
            return_document=ReturnDocument.AFTER,
            upsert=True,
        )
        return updated
