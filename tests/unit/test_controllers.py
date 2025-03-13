"""Tests for the DB controller."""

from unittest.mock import MagicMock

from controllers import MongoController


class TestControllers:
    """Test DB Controllers"""

    def setup_method(self) -> None:
        """Setup method"""
        self.mongo = MongoController(MagicMock())
        self.sdx_topology = {"version": 1, "timestamp": "2024-07-18T15:33:12Z"}

    def test_get_topology(self):
        """Test get_topology"""
        self.mongo.get_topology()
        assert self.mongo.db.sdx_info.find_one.call_count == 1

    def test_upsert_topology(self):
        """Test upsert_topology"""
        self.mongo.upsert_topology(self.sdx_topology)
        assert self.mongo.db.sdx_info.find_one_and_update.call_count == 1
