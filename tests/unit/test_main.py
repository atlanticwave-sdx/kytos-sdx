"""Test Main methods."""
import asyncio
from unittest.mock import MagicMock, patch
from pytest_unordered import unordered

from kytos.core.events import KytosEvent
from kytos.lib.helpers import get_controller_mock, get_test_client

# pylint: disable=import-error
from napps.kytos.sdx.main import Main
from tests.helpers import get_topology, get_converted_topology


# pylint: disable=protected-access
class TestMain:
    """Tests for the Main class."""

    def setup_method(self):
        """Execute steps before each tests."""
        Main.get_mongo_controller = MagicMock()
        self.controller = get_controller_mock()
        self.napp = Main(self.controller)
        #self.napp.oxpo_name = "Ampath-OXP"
        #self.napp.oxpo_url = "ampath.net"
        self.api_client = get_test_client(self.controller, self.napp)
        self.endpoint = "kytos/sdx"

    def test_update_topology_success_case(self):
        """Test update topology method to success case."""
        topology = get_topology()
        expected = get_converted_topology()
        self.napp.sdx_topology = {
            "version": 1, "timestamp": "2024-07-18T15:33:12Z"
        }
        event = KytosEvent(
            name="kytos.topology.updated", content={"topology": topology}
        )
        self.napp.handler_on_topology_updated_event(event)
        assert self.napp._topology == topology
        converted_topo = self.napp._converted_topo
        for node in converted_topo["nodes"]:
            node["ports"] = unordered(node["ports"])
        assert unordered(converted_topo["nodes"]) == expected["nodes"]
        assert unordered(converted_topo["links"]) == expected["links"]
        for attr in ["name", "id", "model_version", "services"]:
            assert attr in converted_topo
            assert converted_topo[attr] == expected[attr]

    async def test_get_topology_response(self, monkeypatch):
        """Test shortest path."""
        self.napp.controller.loop = asyncio.get_running_loop()
        self.napp._converted_topo = {}
        response = await self.api_client.get(f"{self.endpoint}/topology/2.0.0")
        assert response.status_code == 200
        assert response.json() == {}
