"""
Main module of amlight/sdx Kytos Network Application.
"""
import os
import shelve
import requests
import traceback

from kytos.core import KytosNApp, log, rest
from kytos.core.events import KytosEvent
from kytos.core.helpers import listen_to
from kytos.core.rest_api import (HTTPException, JSONResponse, Request,
                                 content_type_json_or_415, get_json_or_400)
from .controllers import MongoController
from .convert_topology import ParseConvertTopology
from .settings import (
    EVENT_TYPES,
    KYTOS_EVC_URL,
    KYTOS_TOPOLOGY_URL,
    KYTOS_TAGS_URL,
)
from .utils import get_timestamp


class Main(KytosNApp):  # pylint: disable=R0904
    """Main class of amlight/sdx NApp.

    This class is the entry point for this NApp.
    """

    def setup(self):
        """Replace the '__init__' method for the KytosNApp subclass.

        The setup method is automatically called by the controller when your
        application is loaded.

        So, if you have any setup routine, insert it here.
        """
        self.sdxlc_url = os.environ.get("SDXLC_URL", "")
        self.oxpo_name = os.environ.get("OXPO_NAME", "")
        self.oxpo_url = os.environ.get("OXPO_URL", "")
        self.mongo_controller = self.get_mongo_controller()
        self.sdx_topology = {}
        # mapping from IDs used by kytos and SDX
        # ex: urn:sdx:port:sax.net:Sax01:40 <--> cc:00:00:00:00:00:00:01:40
        self.kytos2sdx = {}
        self.sdx2kytos = {}
        self.load_sdx_topology()

    def execute(self):
        """Execute once when the napp is running."""

    def shutdown(self):
        """
        Run when your NApp is unloaded.
        If you have some cleanup procedure, insert it here.
        """

    @staticmethod
    def get_mongo_controller():
        """Get MongoController"""
        return MongoController()

    def load_sdx_topology(self):
        self.sdx_topology = self.mongo_controller.get_topology()
        if self.sdx_topology:
            return
        self.sdx_topology = {
            "version": 1,
            "timestamp": get_timestamp(),
        }

    @staticmethod
    def get_kytos_topology():
        """retrieve topology from API"""
        kytos_topology = requests.get(
                KYTOS_TOPOLOGY_URL, timeout=10).json()
        topology = kytos_topology["topology"]
        response = requests.get(
            KYTOS_TAGS_URL, timeout=10)
        if response.status_code != 200:
            return topology
        kytos_tag_ranges = response.json()
        for intf_id, tag_ranges in kytos_tag_ranges.items():
            sw_id = intf_id[:23]
            topology["switches"][sw_id]["interfaces"][intf_id]["tag_ranges"] = (
                tag_ranges["tag_ranges"]["vlan"]
            )
        return topology

    @listen_to(
        "kytos/topology.link_.*",
        "kytos/topology.switch.*",
        pool="dynamic_single"
    )
    def on_topology_event(self, event: KytosEvent):
        """Handler for topology events."""
        self.handler_on_topology_event(event)

    def handler_on_topology_event(self, event: KytosEvent):
        """Handler topology events and filter SDX events of interest."""
        # Sanity checks
        if not event:
            return
        sdx_event_type = EVENT_TYPES.get(event.name)
        if sdx_event_type:
            self.sdx_topology["version"] += 1
            self.sdx_topology["timestamp"] = get_timestamp()
            self.mongo_controller.upsert_topology(self.sdx_topology)
        if sdx_event_type == "oper":
            try:
                topology_converted = self.convert_topology_v2()
                self.post_topology_to_sdxlc(topology_converted)
            except:
                pass

    def convert_topology_v2(self):
        """Convert Kytos topoloty to SDX (v2)."""
        try:
            topology_converted = ParseConvertTopology(
                topology=self.get_kytos_topology(),
                version=self.sdx_topology["version"],
                timestamp=self.sdx_topology["timestamp"],
                oxp_name=self.oxpo_name,
                oxp_url=self.oxpo_url,
            ).parse_convert_topology()
        except Exception as exc:
            err = traceback.format_exc().replace("\n", ", ")
            log.error(f"Convert topology failed: {exc} - Traceback: {err}")
            raise HTTPException(
                424,
                detail="Failed to convert kytos topology - check logs"
            ) from exc

        self.kytos2sdx = topology_converted.pop("kytos2sdx", {})
        self.sdx2kytos = topology_converted.pop("sdx2kytos", {})

        return topology_converted

    def post_topology_to_sdxlc(self, converted_topology):
        """Post converted topology to SDX-LC."""
        try:
            assert self.sdxlc_url, "undefined SDXLC_URL"
            response = requests.post(
                self.sdxlc_url,
                timeout=10,
                json=converted_topology
            )
            assert response.status_code == 200, response.text
        except Exception as exc:
            msg = "Failed to send topoloty to SDX-LC"
            err = traceback.format_exc().replace("\n", ", ")
            log.error(f"{msg}: {exc} - Traceback: {err}")
            raise HTTPException(424, detail=f"{msg} - check logs") from exc

    @rest("topology/2.0.0", methods=["GET"])
    def get_sdx_topology_v2(self, _request: Request) -> JSONResponse:
        """return sdx topology v2"""
        topology_converted = self.convert_topology_v2()
        return JSONResponse(topology_converted)

    @rest("topology/2.0.0", methods=["POST"])
    def send_topology_to_sdxlc(self, _request: Request) -> JSONResponse:
        """Send the topology (v2) to SDX-LC"""
        topology_converted = self.convert_topology_v2()
        send_result = self.post_topology_to_sdxlc(topology_converted)
        return JSONResponse("Operation successful", status_code=200)

    @rest("l2vpn/1.0", methods=["POST"])
    def create_l2vpn(self, request: Request) -> JSONResponse:
        """REST to create L2VPN connection."""
        content = get_json_or_400(request, self.controller.loop)

        # Sanity check: only supports 2 endpoints (PTP L2VPN)
        if len(content["endpoints"]) != 2:
            msg = "Only PTP L2VPN is supported: more than 2 endpoints provided"
            log.warn(f"EVC creation failed ({msg}). request={content}")
            return JSONResponse({"description": msg}, 402)

        evc_dict = {
            "name": content["name"],
            "uni_a": {},
            "uni_z": {},
            "dynamic_backup_path": True,
        }

        for idx, uni in {0: "uni_a", 1: "uni_z"}:
            sdx_id = content["endpoints"][idx]["port_id"]
            kytos_id = self.sdx2kytos.get(sdx_id)
            if not sdx_id or not kytos_id:
                msg = f"Invalid value for endpoints.{idx} ({sdx_id})"
                log.warn(f"EVC creation failed: {msg}. request={content}")
                return JSONResponse({"result": msg}, 400)
            evc_dict[uni]["interface_id"] = kytos_id
            evc_dict[uni]["tag"] = {
                "value": content["endpoints"][idx]["vlan"],
            }

        try:
            kytos_evc_url = os.environ.get(
                "KYTOS_EVC_URL", KYTOS_EVC_URL
            )
            response = requests.post(
                    kytos_evc_url,
                    json=evc_dict,
                    timeout=30)
            assert response.status_code == 201, response.text
        except Exception as exc:
            err = traceback.format_exc().replace("\n", ", ")
            log.warn(f"EVC creation failed: {exc} - {err}")
            raise HTTPException(
                    400,
                    detail=f"Request to Kytos failed: {exc}"
                ) from exc

        return JSONResponse(response.json(), 200)

    @rest("v1/l2vpn_ptp", methods=["POST"])
    def create_l2vpn_ptp(self, request: Request) -> JSONResponse:
        """ REST to create L2VPN ptp connection."""
        content = get_json_or_400(request, self.controller.loop)

        evc_dict = {
            "name": None,
            "uni_a": {},
            "uni_z": {},
            "dynamic_backup_path": True,
        }

        for attr in evc_dict:
            if attr not in content:
                msg = f"missing attribute {attr}"
                log.warn(f"EVC creation failed: {msg}. request={content}")
                return JSONResponse({"result": msg}, 400)
            if "uni_" in attr:
                sdx_id = content[attr].get("port_id")
                kytos_id = self.sdx2kytos.get(sdx_id)
                if not sdx_id or not kytos_id:
                    msg = f"unknown value for {attr}.port_id ({sdx_id})"
                    log.warn(f"EVC creation failed: {msg}. request={content}")
                    return JSONResponse({"result": msg}, 400)
                evc_dict[attr]["interface_id"] = kytos_id
                if "tag" in content[attr]:
                    evc_dict[attr]["tag"] = content[attr]["tag"]
            else:
                evc_dict[attr] = content[attr]

        try:
            kytos_evc_url = os.environ.get(
                "KYTOS_EVC_URL", KYTOS_EVC_URL
            )
            response = requests.post(
                    kytos_evc_url,
                    json=evc_dict,
                    timeout=30)
            assert response.status_code == 201, response.text
        except Exception as exc:
            err = traceback.format_exc().replace("\n", ", ")
            log.warn(f"EVC creation failed: {exc} - {err}")
            raise HTTPException(
                    400,
                    detail=f"Request to Kytos failed: {exc}"
                ) from exc

        return JSONResponse(response.json(), 200)

    @rest("v1/l2vpn_ptp", methods=["DELETE"])
    def delete_l2vpn_ptp(self, request: Request) -> JSONResponse:
        """ REST to create L2VPN ptp connection."""
        content = get_json_or_400(request, self.controller.loop)

        uni_a = content.get("uni_a", {}).get("port_id")
        vlan_a = content.get("uni_a", {}).get("tag", {}).get("value")
        uni_z = content.get("uni_z", {}).get("port_id")
        vlan_z = content.get("uni_z", {}).get("tag", {}).get("value")
        if not all([uni_a, vlan_a, uni_z, vlan_z]):
            msg = (
                "Delete EVC failed: missing attribute."
                f"{uni_a=} {vlan_a=} {uni_z=} {vlan_z=}"
            )
            log.warn(msg)
            return JSONResponse({"result": msg}, 400)

        kuni_a = self.sdx2kytos.get(uni_a)
        kuni_z = self.sdx2kytos.get(uni_z)

        try:
            kytos_evc_url = os.environ.get(
                "KYTOS_EVC_URL", KYTOS_EVC_URL
            )
            response = requests.get(kytos_evc_url, timeout=30)
            assert response.status_code == 200, response.text
            evcs = response.json()
        except Exception as exc:
            err = traceback.format_exc().replace("\n", ", ")
            log.warn(f"EVC query failed on Kytos: {exc} - {err}")
            raise HTTPException(
                    400,
                    detail=f"Request to Kytos failed: {exc}"
                ) from exc

        for evcid, evc in evcs.items():
            if all([
                evc["uni_a"]["interface_id"] == kuni_a,
                evc["uni_a"].get("tag", {}).get("value") == vlan_a,
                evc["uni_z"]["interface_id"] == kuni_z,
                evc["uni_z"].get("tag", {}).get("value") == vlan_z,
            ]):
                break
        else:
            msg = f"EVC not found: {uni_a=} {vlan_a=} {uni_z=} {vlan_z=}"
            log.warn(msg)
            raise HTTPException(400, detail=msg)

        try:
            response = requests.delete(
                f"{kytos_evc_url.rstrip('/')}/{evcid}", timeout=30
            )
            assert response.status_code == 201, response.text
        except Exception as exc:
            err = traceback.format_exc().replace("\n", ", ")
            log.warn(f"Delete EVC failed on Kytos: {exc} - {err}")
            raise HTTPException(
                400, detail=f"Delete EVC failed on Kytos: {exc}"
            ) from exc

        return JSONResponse(response.json(), 200)
