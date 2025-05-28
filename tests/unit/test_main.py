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
    get_evc,
    get_evc_converted,
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

    @patch("requests.get")
    def test_topology_loaded(self, requests_mock):
        """Test topology loaded."""
        expected = get_converted_topology()
        self.napp.sdx_topology = {"version": 1, "timestamp": "2024-07-18T15:33:12Z"}
        mock_res1, mock_res2 = MagicMock(), MagicMock()
        mock_res1.json.return_value = {"topology": get_topology_dict()}
        mock_res2.status_code = 200
        mock_res2.json.return_value = {
            "aa:00:00:00:00:00:00:02:50": {"tag_ranges": {"vlan": [[1, 4094]]}}
        }
        requests_mock.side_effect = [mock_res1, mock_res2]
        self.napp.handler_on_topology_loaded()
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
        # simulate that initially TestSw1 is disabled
        topo_dict = get_topology_dict()
        for sw in topo_dict["switches"].values():
            if sw["data_path"] != "TestSw1":
                continue
            sw["status"] = "DISABLED"
            sw["enabled"] = False
            sw["status_reason"] = ["disabled"]
            for intf in sw["interfaces"].values():
                intf["status"] = "DISABLED"
                intf["enabled"] = False
                intf["status_reason"] = ["disabled"]
        for link in topo_dict["links"].values():
            if all(
                [
                    not link["endpoint_a"]["name"].startswith("TestSw1"),
                    not link["endpoint_b"]["name"].startswith("TestSw1"),
                ]
            ):
                continue
            link["status"] = "DISABLED"
            link["enabled"] = False
            link["status_reason"] = ["disabled"]

        self.napp._topo_dict = topo_dict
        self.napp.sdx_topology = {"version": 1, "timestamp": "2024-07-18T15:33:12Z"}

        # now send an update with TestSw1 enabled and TestSw2 down
        topology = get_topology()
        topology.switches["aa:00:00:00:00:00:00:02"].is_active.return_value = False
        topology.switches["aa:00:00:00:00:00:00:02"].metadata["lat"] = "26.37"

        event = KytosEvent(
            name="kytos.topology.updated", content={"topology": topology}
        )
        self.napp.handler_on_topology_updated_event(event)
        assert self.napp._topology == topology
        assert self.napp.sdx_topology["version"] == 2
        requests_mock.assert_called()

        # Expected converted topology: all items related to
        # aa:00:00:00:00:00:00:02/TestSw2 should be down and latitude changed
        expected = get_converted_topology()
        for node in expected["nodes"]:
            if node["name"] == "TestSw2":
                node["status"] = "down"
                node["location"]["latitude"] = 26.37
                break

        converted_topo = self.napp._converted_topo
        for node in converted_topo["nodes"]:
            node["ports"] = unordered(node["ports"])
        assert unordered(converted_topo["nodes"]) == expected["nodes"]
        assert unordered(converted_topo["links"]) == expected["links"]

    @patch("time.sleep", return_value=None)
    def test_update_topology_metadata_success_case(self, _):
        """Test update metadata method to success case."""
        self.napp._topo_dict = get_topology_dict()
        self.napp.sdx_topology = {"version": 1, "timestamp": "2024-07-18T15:33:12Z"}
        topology = get_topology()
        # switch and interface metadata changes
        # switch metadata
        switch = topology.switches["aa:00:00:00:00:00:00:02"]
        switch.metadata["iso3166_2_lvl4"] = "US-CA"
        event = KytosEvent(
            name="kytos/topology.switches.metadata.added",
            content={"switch": switch, "metadata": switch.metadata.copy()},
        )
        self.napp.handle_metadata_event(event)
        assert self.napp.sdx_topology["version"] == 2
        # interface metadata
        interface = switch.interfaces["aa:00:00:00:00:00:00:02:50"]
        interface.metadata["entities"] = ["Test1", "this is a test"]
        event = KytosEvent(
            name="kytos/topology.interfaces.metadata.added",
            content={"interface": interface, "metadata": interface.metadata.copy()},
        )
        self.napp.handle_metadata_event(event)
        assert self.napp.sdx_topology["version"] == 3
        # now check the content
        res_sw = next(
            filter(
                lambda sw: sw["name"] == "TestSw2", self.napp._converted_topo["nodes"]
            )
        )
        assert res_sw["location"]["iso3166_2_lvl4"] == "US-CA"
        res_intf = next(
            filter(lambda intf: intf["name"] == "TestSw2-eth50", res_sw["ports"])
        )
        assert res_intf["entities"] == ["Test1", "this is a test"]

        # link metadata
        link = topology.links[
            "4b7b34ca81ef25f18b453f6ea2f4ed328d9db4beba0e6b2eeab3dd2441f3b36b"
        ]
        link.metadata["residual_bandwidth"] = 90
        event = KytosEvent(
            name="kytos/topology.links.metadata.added",
            content={"link": link, "metadata": link.metadata.copy()},
        )
        self.napp.handle_metadata_event(event)
        assert self.napp.sdx_topology["version"] == 4
        res_link = next(
            filter(
                lambda link: link["name"] == "TestSw2/3_TestSw3/3",
                self.napp._converted_topo["links"],
            )
        )
        assert res_link["residual_bandwidth"] == 90

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

    def test_handler_on_topology_loaded(self):
        """Test handler_on_topology_loaded."""
        self.napp.get_kytos_topology = MagicMock()
        some_topo = {"switches": {"dpid1": {}}, "links": {"link1": {}}}
        self.napp.get_kytos_topology.return_value = some_topo
        self.napp.convert_topology_v2 = MagicMock()
        self.napp.handler_on_topology_loaded()
        assert self.napp._topo_dict == some_topo

    @patch("requests.post")
    @patch("requests.patch")
    async def test_update_l2vpn(self, req_patch_mock, req_post_mock):
        """Test update a l2vpn."""
        req_patch_mock.return_value = MagicMock(status_code=200)
        req_post_mock.return_value = MagicMock(status_code=201)
        self.napp.controller.loop = asyncio.get_running_loop()
        self.napp.sdx2kytos = {
            "urn:sdx:port:testoxp.net:TestSw3:50": "aa:00:00:00:00:00:00:03:50",
            "urn:sdx:port:testoxp.net:TestSw1:40": "aa:00:00:00:00:00:00:01:40",
        }
        payload = {
            "endpoints": [
                {"port_id": "urn:sdx:port:testoxp.net:TestSw3:50", "vlan": "501"},
                {"port_id": "urn:sdx:port:testoxp.net:TestSw1:40", "vlan": "600"},
            ],
            "description": "changed!",
        }
        response = await self.api_client.patch(
            f"{self.endpoint}/l2vpn/1.0/a123",
            json=payload,
        )
        assert response.status_code == 201

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

        # test 2: invalid payload
        payload["uni_a"]["tag"]["value"] = "invalid"
        response = await self.api_client.post(
            f"{self.endpoint}/v1/l2vpn_ptp",
            json=payload,
        )
        assert response.status_code == 400

        # test 3: testing with VLAN 'all'
        payload["uni_a"]["tag"]["value"] = "all"
        response = await self.api_client.post(
            f"{self.endpoint}/v1/l2vpn_ptp",
            json=payload,
        )
        assert response.status_code == 200
        requests_mock.assert_called_with(json={})


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
        assert vlan == [[1, 100]]
        assert msg is None
        # case 5: range - invalid
        vlan, msg = self.napp.parse_vlan("1:9999")
        assert vlan is None
        assert "Invalid vlan" in msg

    @patch("requests.get")
    async def test_get_l2vpn_api(self, req_get_mock):
        """Test get a l2vpn using API."""
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.json.return_value = get_evc()
        req_get_mock.return_value = mock_res
        self.napp.controller.loop = asyncio.get_running_loop()
        self.napp.kytos2sdx = {
            "aa:00:00:00:00:00:00:03:50": "urn:sdx:port:ampath.net:Ampath3:50",
            "aa:00:00:00:00:00:00:02:40": "urn:sdx:port:ampath.net:Ampath2:40",
        }
        response = await self.api_client.request(
            "GET",
            f"{self.endpoint}/l2vpn/1.0/88c326c7e70d49",
        )
        assert response.status_code == 200
        assert response.json() == get_evc_converted()
