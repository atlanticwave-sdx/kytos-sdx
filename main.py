"""
Main module of amlight/sdx Kytos Network Application.
"""
import os
import shelve
import requests
import traceback
import threading
import time
from copy import deepcopy
from collections import defaultdict

from kytos.core import KytosNApp, log, rest
from kytos.core.events import KytosEvent
from kytos.core.helpers import listen_to
from kytos.core.rest_api import (HTTPException, JSONResponse, Request,
                                 content_type_json_or_415, get_json_or_400)
from .controllers import MongoController
from .convert_topology import ParseConvertTopology
from .settings import (
    SDXLC_URL,
    OXPO_NAME,
    OXPO_URL,
    KYTOS_EVC_URL,
    KYTOS_TOPOLOGY_URL,
    KYTOS_TAGS_URL,
    TOPOLOGY_EVENT_WAIT,
)
from .utils import get_timestamp

MIN_TIME = "0000-00-00T00:00:00Z"
MAX_TIME = "9999-99-99T99:99:99Z"

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
        self.sdxlc_url = os.environ.get("SDXLC_URL", SDXLC_URL)
        self.oxpo_name = os.environ.get("OXPO_NAME", OXPO_NAME)
        self.oxpo_url = os.environ.get("OXPO_URL", OXPO_URL)
        self.mongo_controller = self.get_mongo_controller()
        self.sdx_topology = {}
        # _topology, _topo_ts, _topo_wait, _topo_lock, _topo_handler_lock:
        # those variables are used to keep track of topology updates, because
        # kytos does not provide specific events topology#43
        self._topology = None
        self._topology_updated_at = None
        self._converted_topo = None
        self._topo_dict = {"switches": {}, "links": {}}
        self._topo_ts = 0
        self._topo_max_wait = TOPOLOGY_EVENT_WAIT
        self._topo_wait = 1
        self._topo_lock = threading.Lock()
        self._topo_handler_lock = threading.Lock()
        # mapping from IDs used by kytos and SDX
        # ex: urn:sdx:port:sax.net:Sax01:40 <--> cc:00:00:00:00:00:00:01:40
        self.kytos2sdx = {}
        self.sdx2kytos = {}
        self.load_sdx_topology()

    def execute(self):
        """Execute once when the napp is running."""

    def shutdown(self):
        """Run when your NApp is unloaded."""

    @staticmethod
    def get_mongo_controller():
        """Get MongoController"""
        return MongoController()

    def load_sdx_topology(self):
        self.sdx_topology = self.mongo_controller.get_topology()
        if not self.sdx_topology:
            self.sdx_topology = {
                "version": 1,
                "timestamp": get_timestamp(),
            }
        with self._topo_lock:
            self._topo_dict = self.get_kytos_topology()
            self._converted_topo = self.convert_topology_v2()

    @staticmethod
    def get_kytos_topology():
        """retrieve topology from API"""
        try:
            kytos_topology = requests.get(
                KYTOS_TOPOLOGY_URL, timeout=10).json()
            topology = kytos_topology["topology"]
            response = requests.get(
                KYTOS_TAGS_URL, timeout=10)
        except:
            return {"switches": {}, "links": {}}
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
        "kytos/topology.updated",
        "kytos/topology.topology_loaded",
    )
    def on_topology_updated_event(self, event: KytosEvent):
        """Handler for topology updated events."""
        self.handler_on_topology_updated_event(event)

    def handler_on_topology_updated_event(self, event: KytosEvent):
        """Handler topology updated event."""
        with self._topo_lock:
            if (
                self._topology_updated_at
                and self._topology_updated_at > event.timestamp
            ):
                return
            self._topology = event.content["topology"]
            self._topology_updated_at = event.timestamp
        if self._topo_handler_lock.locked():
            self._topo_wait = min(self._topo_wait+1, self._topo_max_wait)
            return
        self._topo_wait = 1
        with self._topo_handler_lock:
            waited = 0
            step_wait = 0.2
            while waited <= self._topo_wait:
                waited += step_wait
                time.sleep(step_wait)
        with self._topo_lock:
            self.update_topology()

    def update_topology(self):
        """Process the topology from Kytos event"""
        admin_change = False
        oper_change = False
        old_switches = {k:None for k in self._topo_dict["switches"]}
        for switch in self._topology.switches.values():
            old_switches.pop(switch.id, None)
            switch_dict = self._topo_dict["switches"].get(switch.id)
            if not switch_dict:
                # XXX: deepcopy has performance impacts but it is needed here
                # because we need to be able to compare with old values
                self._topo_dict["switches"][switch.id] = deepcopy(switch.as_dict())
                admin_change = True
                continue
            if switch.is_active() != switch_dict["active"]:
                oper_change = True
                switch_dict["active"] = switch.is_active()
            if switch.is_enabled() != switch_dict["enabled"]:
                admin_change = True
                switch_dict["enabled"] = switch.is_enabled()
            if self.try_update_attrs(switch, switch_dict):
                admin_change = True
            if self.try_update_metadata(switch, switch_dict["metadata"]):
                admin_change = True
            old_intfs = {k:None for k in switch_dict["interfaces"]}
            for intf in switch.interfaces.values():
                old_intfs.pop(intf.id, None)
                intf_dict = switch_dict["interfaces"].get(intf.id)
                if not intf_dict:
                    switch_dict["interfaces"][intf.id] = deepcopy(intf.as_dict())
                    admin_change = True
                    continue
                if intf.is_active() != intf_dict["active"]:
                    oper_change = True
                    intf_dict["active"] = intf.is_active()
                if intf.is_enabled() != intf_dict["enabled"]:
                    admin_change = True
                    intf_dict["enabled"] = intf.is_enabled()
                if self.try_update_attrs(intf, intf_dict):
                    admin_change = True
                if self.try_update_metadata(intf, intf_dict["metadata"]):
                    admin_change = True
                intf_dict["tag_ranges"] = intf.tag_ranges["vlan"]
            if old_intfs:
                admin_change = True
                for intf_id in old_intfs:
                    switch_dict["interfaces"].pop(intf_id)
        if old_switches:
            admin_change = True
            for sw_id in old_switches:
                self._topo_dict["switches"].pop(sw_id)

        # Links
        old_links = {k:None for k in self._topo_dict["links"]}
        for link in self._topology.links.values():
            old_links.pop(link.id, None)
            link_dict = self._topo_dict["links"].get(link.id)
            if not link_dict:
                self._topo_dict["links"][link.id] = deepcopy(link.as_dict())
                admin_change = True
                continue
            if link.is_active() != link_dict["active"]:
                oper_change = True
                link_dict["active"] = link.is_active()
            if link.is_enabled() != link_dict["enabled"]:
                admin_change = True
                link_dict["enabled"] = link.is_enabled()
            if self.try_update_attrs(link, link_dict):
                admin_change = True
            if self.try_update_metadata(link, link_dict["metadata"]):
                admin_change = True
        if old_links:
            admin_change = True
            for link_id in old_links:
                self._topo_dict["links"].pop(link_id)

        if not admin_change and not oper_change:
            return
        if admin_change:
            self.sdx_topology["version"] += 1
        self.sdx_topology["timestamp"] = get_timestamp()
        self.mongo_controller.upsert_topology(self.sdx_topology)
        self._converted_topo = self.convert_topology_v2()
        if oper_change:
            try:
                self.post_topology_to_sdxlc(self._converted_topo)
            except:
                pass

    @listen_to(
        "kytos/topology.(switches|interfaces|links).metadata.*",
    )
    def on_metadata_event(self, event: KytosEvent):
        """Handler for metadata change events."""
        with self._topo_lock:
            self.handle_metadata_event(event)

    def handle_metadata_event(self, event: KytosEvent):
        """Handler for metadata change events."""
        # get obj_type and action, convert plural to singular, get object
        # switches|interfaces|links -> switch|interface|link
        _, obj_type, _, action = event.name.split(".")
        obj_type = obj_type[:-1].replace("che", "ch")
        obj = event.content[obj_type]
        if obj_type == "switch":
            obj_dict = self._topo_dict["switches"].get(obj.id)
        elif obj_type == "link":
            obj_dict = self._topo_dict["links"].get(obj.id)
        else:
            switch_dict = self._topo_dict["switches"].get(obj.id[:23])
            if not switch_dict or obj.id not in switch_dict["interfaces"]:
                log.warn(f"Metadata event for unknown obj {obj.id} event={event.name}")
                return
            obj_dict = switch_dict["interfaces"][obj.id]

        if not self.try_update_metadata(obj, obj_dict["metadata"]):
            return

        self.sdx_topology["version"] += 1
        self.sdx_topology["timestamp"] = get_timestamp()
        self.mongo_controller.upsert_topology(self.sdx_topology)
        self._converted_topo = self.convert_topology_v2()

    def try_update_metadata(self, obj, saved_metadata):
        """Try to update metadata for an entity."""
        metadata_changed = False
        metadata_interest = [
            # link metadata
            "link_name"
            "availability",
            "packet_loss",
            "latency",
            "residual_bandwidth",
            # switch metadata
            "node_name",
            "iso3166_2_lvl4",
            "lng",
            "lat",
            "address",
            # interface metadata
            "port_name",
            "sdx_vlan_range",
            "sdx_nni",
            "mtu",
        ]

        for attr in metadata_interest:
            old_value = saved_metadata.get(attr)
            new_value = obj.metadata.get(attr)
            if old_value == new_value:
                continue
            metadata_changed = True
            if new_value is not None:
                saved_metadata[attr] = new_value
            else:
                saved_metadata.pop(attr, None)
        return metadata_changed

    def try_update_attrs(self, obj, saved_dict):
        """Try to update attribute for an object."""
        attr_changed = False
        attr_interest = [
            # link attrs
            # endpoint?
            # switch attrs
            "name",
            "data_path",
            # interface attrs
            "nni",
            "speed",
            "link",
        ]
        obj_dict = obj.as_dict()
        for attr in attr_interest:
            old_value = saved_dict.get(attr)
            new_value = obj_dict.get(attr)
            if old_value == new_value:
                continue
            attr_changed = True
            saved_dict[attr] = new_value
        return attr_changed

    def convert_topology_v2(self):
        """Convert Kytos topoloty to SDX (v2)."""
        try:
            topology_converted = ParseConvertTopology(
                topology=self._topo_dict,
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
        return JSONResponse(self._converted_topo)

    @rest("topology/2.0.0", methods=["POST"])
    def send_topology_to_sdxlc(self, _request: Request) -> JSONResponse:
        """Send the topology (v2) to SDX-LC"""
        send_result = self.post_topology_to_sdxlc(self._converted_topo)
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
        if "state" in content:
            msg = "Attribute 'state' not supported for L2VPN creation"
            log.warn(f"EVC creation failed ({msg}). request={content}")
            return JSONResponse({"description": msg}, 422)
        sched_start = content.get("scheduling", {}).get("start_time", MIN_TIME)
        sched_end = content.get("scheduling", {}).get("end_time", MAX_TIME)
        if sched_start >= sched_end:
            msg = "Invalid scheduling: end_time must be greater than start_time"
            log.warn(f"EVC creation failed ({msg}). request={content}")
            return JSONResponse({"description": msg}, 411)
        if "max_number_oxps" in content.get("qos_metrics", {}):
            msg = "Invalid qos_metrics.max_number_oxps for OXP"
            log.warn(f"EVC creation failed ({msg}). request={content}")
            return JSONResponse({"description": msg}, 422)

        evc_dict = {
            "name": content["name"],
            "uni_a": {},
            "uni_z": {},
            "dynamic_backup_path": True,
            "metadata": {},
            "primary_constraints": {},
            "secondary_constraints": {},
        }

        for idx, uni in {0: "uni_a", 1: "uni_z"}.items():
            sdx_id = content["endpoints"][idx]["port_id"]
            kytos_id = self.sdx2kytos.get(sdx_id)
            if not sdx_id or not kytos_id:
                msg = f"Invalid value for endpoints.{idx} ({sdx_id})"
                log.warn(f"EVC creation failed: {msg}. request={content}")
                return JSONResponse({"description": msg}, 400)
            evc_dict[uni]["interface_id"] = kytos_id
            # sdx_vlan: some conversion from sdx -> kytos must be done for VLAN
            # "xx" -> xx: VLAN ID integer
            # "all" -> <no-tag>: on Kytos that would be a EPL (no tag)
            # "any" -> Not Supported! the OXPO wont choose the VLAN, not supported
            # "untagged" -> untagged: no conversion
            # "xx:yy" -> [xx, yy]: VLAN range
            sdx_vlan = content["endpoints"][idx]["vlan"]
            if sdx_vlan.isdigit():
                sdx_vlan = int(sdx_vlan)
                if sdx_vlan < 1 or sdx_vlan > 4095:
                    msg = f"Invalid vlan on endpoints.{idx} (0 > vlan < 4096)"
                    log.warn(f"EVC creation failed: {msg}. request={content}")
                    return JSONResponse({"description": msg}, 422)
            elif sdx_vlan == "all":
                continue
            elif sdx_vlan == "any":
                msg = f"Invalid vlan 'any': not supported on endpoints.{idx}"
                log.warn(f"EVC creation failed: {msg}. request={content}")
                return JSONResponse({"description": msg}, 422)
            elif sdx_vlan == "untagged":
                # nothing to do
                pass
            else:  # assuming vlan range
                try:
                    start, end = sdx_vlan.split(":")
                    sdx_vlan = [int(start), int(end)]
                    assert sdx_vlan[0] < sdx_vlan[1]
                except:
                    msg = f"Invalid vlan range on endpoints.{idx} ({sdx_vlan})"
                    log.warn(f"EVC creation failed: {msg}. request={content}")
                    return JSONResponse({"description": msg}, 422)
            evc_dict[uni]["tag"] = {
                "tag_type": "vlan",
                "value": sdx_vlan,
            }

        if "description" in content:
            evc_dict["metadata"]["sdx_description"] = content["description"]
        if "notifications" in content:
            evc_dict["metadata"]["sdx_notifications"] = content["notifications"]
        if sched_start != MIN_TIME:
            evc_dict["circuit_scheduler"] = [
                {"date": sched_start, "action": "create"}
            ]
        if sched_end != MAX_TIME:
            evc_dict.setdefault("circuit_scheduler", [])
            evc_dict["circuit_scheduler"].append(
                {"date": sched_end, "action": "remove"}
            )
        min_bw = content.get("qos_metrics", {}).get("min_bw")
        if min_bw:
            metrict_type = "mandatory_metrics" if min_bw.get("strict", False) else "flexible_metrics"
            evc_dict["primary_constraints"].setdefault(metrict_type, {})
            evc_dict["primary_constraints"][metrict_type]["bandwidth"] = min_bw["value"]
            evc_dict["secondary_constraints"].setdefault(metrict_type, {})
            evc_dict["secondary_constraints"][metrict_type]["bandwidth"] = min_bw["value"]
        max_delay = content.get("qos_metrics", {}).get("max_delay")
        if max_delay:
            metrict_type = "mandatory_metrics" if max_delay.get("strict", False) else "flexible_metrics"
            evc_dict["primary_constraints"].setdefault(metrict_type, {})
            evc_dict["primary_constraints"][metrict_type]["delay"] = max_delay["value"]
            evc_dict["secondary_constraints"].setdefault(metrict_type, {})
            evc_dict["secondary_constraints"][metrict_type]["delay"] = min_bw["value"]

        # TODO: error handling
        # 401: Not Authorized
        # 409: L2VPN Service already exists.
        # 410: Can't fulfill the strict QoS requirements
        # 411: Scheduling not possible

        try:
            kytos_evc_url = os.environ.get(
                "KYTOS_EVC_URL", KYTOS_EVC_URL
            )
            response = requests.post(
                    kytos_evc_url,
                    json=evc_dict,
                    timeout=30)
            assert response.status_code == 201, response.text
            circuit_id = response.json()["circuit_id"]
        except Exception as exc:
            err = traceback.format_exc().replace("\n", ", ")
            log.warn(f"EVC creation failed: {exc} - {err}")
            return JSONResponse({"description": "L2VPN creation failed: check logs"}, 400)

        return JSONResponse({"service_id": circuit_id}, 201)

    @rest("l2vpn/1.0/{service_id}", methods=["DELETE"])
    def delete_l2vpn(self, request: Request) -> JSONResponse:
        """ REST to delete L2VPN."""
        evcid = request.path_params["service_id"]

        try:
            kytos_evc_url = os.environ.get(
                "KYTOS_EVC_URL", KYTOS_EVC_URL
            )
            response = requests.delete(
                f"{kytos_evc_url.rstrip('/')}/{evcid}", timeout=30
            )
        except Exception as exc:
            err = traceback.format_exc().replace("\n", ", ")
            log.warn(f"Delete EVC failed on Kytos: {exc} - {err}")
            raise HTTPException(
                400, detail=f"Delete EVC failed on Kytos: {exc}"
            ) from exc

        if response.status_code == 404:
            return JSONResponse(
                {"description": "L2VPN Service ID provided does not exist"}, 404
            )
        elif response.status_code != 200:
            log.warn(f"Delete EVC failed on Kytos: {response.text}")
            return JSONResponse(
                {"description": "Failed to delete L2VPN service"}, 400
            )

        return JSONResponse("L2VPN Deleted", 201)

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
            assert response.status_code == 200, response.text
        except Exception as exc:
            err = traceback.format_exc().replace("\n", ", ")
            log.warn(f"Delete EVC failed on Kytos: {exc} - {err}")
            raise HTTPException(
                400, detail=f"Delete EVC failed on Kytos: {exc}"
            ) from exc

        return JSONResponse(response.json(), 200)
