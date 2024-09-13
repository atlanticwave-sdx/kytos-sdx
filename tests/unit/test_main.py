"""Test Main methods."""

import asyncio
from unittest.mock import MagicMock, patch

from pytest_unordered import unordered

from kytos.core.events import KytosEvent
from kytos.lib.helpers import get_controller_mock, get_test_client

# pylint: disable=import-error
from napps.kytos.sdx.main import Main
from napps.kytos.sdx.tests.helpers import (
    get_converted_topology,
    get_topology,
    get_topology_dict,
)


# pylint: disable=protected-access
class TestMain:
    """Tests for the Main class."""

    def setup_method(self):
        """Execute steps before each tests."""
        Main.get_mongo_controller = MagicMock()
        self.controller = get_controller_mock()
        self.napp = Main(self.controller)
        self.api_client = get_test_client(self.controller, self.napp)
        self.endpoint = "kytos/sdx"

    @patch("time.sleep", return_value=None)
    def test_update_topology_success_case(self, _):
        """Test update topology method to success case."""
        topology = get_topology()
        expected = get_converted_topology()
        self.napp.sdx_topology = {"version": 1, "timestamp": "2024-07-18T15:33:12Z"}
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

    @patch("time.sleep", return_value=None)
    @patch("requests.post")
    def test_update_topology_existing_data(self, requests_mock, _):
        """Test update topology with existing data."""
        self.napp._topo_dict = get_topology_dict()
        self.napp.sdx_topology = {"version": 1, "timestamp": "2024-07-18T15:33:12Z"}
        topology = get_topology()
        topology.switches["aa:00:00:00:00:00:00:02"].is_active.return_value = False
        topology.switches["aa:00:00:00:00:00:00:02"].disable()
        topology.switches["aa:00:00:00:00:00:00:02"].metadata["lat"] = "26.37"

        event = KytosEvent(
            name="kytos.topology.updated", content={"topology": topology}
        )
        self.napp.handler_on_topology_updated_event(event)
        assert self.napp._topology == topology
        assert self.napp.sdx_topology["version"] == 2
        requests_mock.assert_called()

    async def test_get_topology_response(self):
        """Test shortest path."""
        self.napp.controller.loop = asyncio.get_running_loop()
        self.napp._converted_topo = {}
        response = await self.api_client.get(f"{self.endpoint}/topology/2.0.0")
        assert response.status_code == 200
        assert response.json() == {}

    @patch("requests.post")
    async def test_create_l2vpn(self, requests_mock):
        """Test create a l2vpn."""
        response_mock = MagicMock()
        response_mock.status_code = 201
        response_mock.json.return_value = {"circuit_id": "a123"}
        requests_mock.return_value = response_mock
        self.napp.controller.loop = asyncio.get_running_loop()
        self.napp.sdx2kytos = {
            "urn:sdx:port:testoxp.net:TestSw3:50": "aa:00:00:00:00:00:00:03:50",
            "urn:sdx:port:testoxp.net:TestSw1:40": "aa:00:00:00:00:00:00:01:40",
        }
        payload = {
            "name": "Vlan_test_123",
            "endpoints": [
                {"port_id": "urn:sdx:port:testoxp.net:TestSw3:50", "vlan": "501"},
                {"port_id": "urn:sdx:port:testoxp.net:TestSw1:40", "vlan": "501"},
            ],
            "description": "test foobar xpto aa bbb",
            "scheduling": {
                "start_time": "2024-08-07T19:55:00Z",
                "end_time": "2024-08-07T19:58:00Z",
            },
            "notifications": [
                {"email": "user@domain.com"},
                {"email": "user2@domain2.com"},
            ],
            "qos_metrics": {
                "min_bw": {"value": 5, "strict": False},
                "max_delay": {"value": 150, "strict": True},
            },
        }
        response = await self.api_client.post(
            f"{self.endpoint}/l2vpn/1.0",
            json=payload,
        )
        assert response.status_code == 201
        assert response.json() == {"service_id": "a123"}

    @patch("requests.delete")
    async def test_delete_l2vpn(self, requests_mock):
        """Test delete a l2vpn."""
        response_mock = MagicMock()
        response_mock.status_code = 200
        requests_mock.return_value = response_mock
        self.napp.controller.loop = asyncio.get_running_loop()
        response = await self.api_client.delete(
            f"{self.endpoint}/l2vpn/1.0/a123",
        )
        assert response.status_code == 201

    @patch("requests.post")
    async def test_create_l2vpn_old_api(self, requests_mock):
        """Test create a l2vpn using old API."""
        response_mock = MagicMock()
        response_mock.status_code = 201
        response_mock.json.return_value = {"circuit_id": "a123"}
        requests_mock.return_value = response_mock
        self.napp.controller.loop = asyncio.get_running_loop()
        self.napp.sdx2kytos = {
            "urn:sdx:port:testoxp.net:TestSw3:50": "aa:00:00:00:00:00:00:03:50",
            "urn:sdx:port:testoxp.net:TestSw1:40": "aa:00:00:00:00:00:00:01:40",
        }
        payload = {
            "name": "Vlan_test_123",
            "uni_a": {
                "port_id": "urn:sdx:port:testoxp.net:TestSw3:50",
                "tag": {"value": 501, "tag_type": 1},
            },
            "uni_z": {
                "port_id": "urn:sdx:port:testoxp.net:TestSw1:40",
                "tag": {"value": 501, "tag_type": 1},
            },
            "dynamic_backup_path": True,
        }
        response = await self.api_client.post(
            f"{self.endpoint}/v1/l2vpn_ptp",
            json=payload,
        )
        assert response.status_code == 200
        assert response.json() == {"circuit_id": "a123"}

    @patch("requests.get")
    @patch("requests.delete")
    async def test_delete_l2vpn_old_api(self, req_del_mock, req_get_mock):
        """Test create a l2vpn using old API."""
        res_get_mock = MagicMock()
        res_get_mock.status_code = 200
        res_get_mock.json.return_value = {
            "a123": {
                "uni_a": {
                    "interface_id": "aa:00:00:00:00:00:00:03:50",
                    "tag": {"value": 501, "tag_type": 1},
                },
                "uni_z": {
                    "interface_id": "aa:00:00:00:00:00:00:01:40",
                    "tag": {"value": 501, "tag_type": 1},
                },
            }
        }
        req_get_mock.return_value = res_get_mock
        self.napp.controller.loop = asyncio.get_running_loop()
        res_del_mock = MagicMock()
        res_del_mock.status_code = 200
        res_del_mock.json.return_value = {"result": "Deleted"}
        req_del_mock.return_value = res_del_mock
        self.napp.sdx2kytos = {
            "urn:sdx:port:testoxp.net:TestSw3:50": "aa:00:00:00:00:00:00:03:50",
            "urn:sdx:port:testoxp.net:TestSw1:40": "aa:00:00:00:00:00:00:01:40",
        }
        payload = {
            "name": "Vlan_test_123",
            "uni_a": {
                "port_id": "urn:sdx:port:testoxp.net:TestSw3:50",
                "tag": {"value": 501, "tag_type": 1},
            },
            "uni_z": {
                "port_id": "urn:sdx:port:testoxp.net:TestSw1:40",
                "tag": {"value": 501, "tag_type": 1},
            },
            "dynamic_backup_path": True,
        }
        response = await self.api_client.request(
            "DELETE",
            f"{self.endpoint}/v1/l2vpn_ptp",
            json=payload,
        )
        assert response.status_code == 200

    def test_parse_vlan(self):
        """Test parse_vlan()."""
        # case 1: invalid
        vlan, msg = self.napp.parse_vlan("9999")
        assert vlan is None
        assert "Invalid vlan" in msg
        # case 2: all - valid
        vlan, msg = self.napp.parse_vlan("all")
        assert vlan == 0
        assert msg is None
        # case 3: untagged - valid
        vlan, msg = self.napp.parse_vlan("untagged")
        assert vlan == "untagged"
        assert msg is None
        # case 4: range - valid
        vlan, msg = self.napp.parse_vlan("1:100")
        assert vlan == [1, 100]
        assert msg is None
        # case 5: range - invalid
        vlan, msg = self.napp.parse_vlan("1:9999")
        assert vlan is None
        assert "Invalid vlan" in msg
