"""
Main module of amlight/sdx Kytos Network Application.
"""

import os
import shelve
import requests
from napps.kytos.sdx_topology.convert_topology import (
    ParseConvertTopology,
)  # pylint: disable=E0401
from napps.kytos.sdx_topology import settings, utils  # pylint: disable=E0401

from kytos.core import KytosNApp, log, rest
from kytos.core.events import KytosEvent
from kytos.core.helpers import listen_to
from kytos.core.rest_api import (
    HTTPException,
    JSONResponse,
    Request,
    content_type_json_or_415,
    get_json_or_400,
)


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
        self.event_info = {}  # pylint: disable=W0201
        self.sdx_topology = {}  # pylint: disable=W0201
        self.shelve_loaded = False  # pylint: disable=W0201
        self.version_control = False  # pylint: disable=W0201
        self.sdxlc_url = os.environ.get("SDXLC_URL", "")
        self.oxpo_name = os.environ.get("OXPO_NAME", "")
        self.oxpo_url = os.environ.get("OXPO_URL", "")
        # mapping from IDs used by kytos and SDX
        # ex: urn:sdx:port:sax.net:Sax01:40 <--> cc:00:00:00:00:00:00:01:40
        self.kytos2sdx = {}
        self.sdx2kytos = {}

    def execute(self):
        """Run after the setup method execution.

        You can also use this method in loop mode if you add to the above setup
        method a line like the following example:

            self.execute_as_loop(30)  # 30-second interval.
        """
        self.load_shelve()

    def shutdown(self):
        """Run when your NApp is unloaded.

        If you have some cleanup procedure, insert it here.
        """

    @listen_to("kytos/topology.unloaded")
    def unload_topology(self):  # pylint: disable=W0613
        """Function meant for validation, to make sure that the shelve
        has been loaded before all the other functions that use it begins to
        call it."""
        self.shelve_loaded = False  # pylint: disable=W0201

    @staticmethod
    def get_kytos_topology():
        """retrieve topology from API"""
        kytos_topology = requests.get(settings.KYTOS_TOPOLOGY_URL, timeout=10).json()
        topology = kytos_topology["topology"]
        response = requests.get(settings.KYTOS_TAGS_URL, timeout=10)
        if response.status_code != 200:
            return topology
        kytos_tag_ranges = response.json()
        for intf_id, tag_ranges in kytos_tag_ranges.items():
            sw_id = intf_id[:23]
            topology["switches"][sw_id]["interfaces"][intf_id]["tag_ranges"] = (
                tag_ranges["tag_ranges"]
            )
        return topology

    def post_sdx_lc(self, event_type=None):
        """return the status from post sdx topology to sdx lc"""
        # if not SDXLC is configured we ignore this part
        if not self.sdxlc_url:
            return {"result": self.sdx_topology, "status_code": 200}

        post_topology = requests.post(
            self.sdxlc_url, timeout=60, json=self.sdx_topology
        )
        if post_topology.status_code == 200:
            if event_type is not None:
                return {
                    "result": self.sdx_topology,
                    "status_code": post_topology.status_code,
                }
        return {
            "result": post_topology.json(),
            "status_code": post_topology.status_code,
        }

    def validate_sdx_topology(self):
        """return 200 if validated topology following the SDX data model"""
        try:
            sdx_topology_validator = os.environ.get("SDXTOPOLOGY_VALIDATOR")
            if sdx_topology_validator == "disabled":
                return {"result": "disabled", "status_code": 200}
            response = requests.post(
                sdx_topology_validator, json=self.sdx_topology, timeout=10
            )
        except ValueError as exception:
            log.info("validate topology result %s %s", exception, 401)
            raise HTTPException(
                401, detail=f"Path is not valid: {exception}"
            ) from exception
        result = response.json()
        return {"result": response.json(), "status_code": response.status_code}

    def convert_topology(self, event_type=None, event_timestamp=None):
        """Function that will take care of update the shelve containing
        the version control that will be updated every time a change is
        detected in kytos topology, and return a new sdx topology"""
        try:
            with shelve.open("topology_shelve") as open_shelve:
                version = open_shelve["version"]
                self.dict_shelve = dict(open_shelve)  # pylint: disable=W0201
                open_shelve.close()
            if version >= 0 and event_type is not None:
                if event_type == "administrative":
                    timestamp = utils.get_timestamp()
                    version += 1
                elif event_type == "operational":
                    timestamp = event_timestamp
                else:
                    return {"result": {}, "status_code": 401}
                topology_converted = ParseConvertTopology(
                    topology=self.get_kytos_topology(),
                    version=version,
                    timestamp=timestamp,
                    model_version=self.dict_shelve["model_version"],
                    oxp_name=self.dict_shelve["name"],
                    oxp_url=self.dict_shelve["url"],
                ).parse_convert_topology()
                return {"result": topology_converted, "status_code": 200}
            return {"result": {}, "status_code": 401}
        except Exception as err:  # pylint: disable=W0703
            log.info("validation Error, status code 401:", err)
            return {"result": "Validation Error", "status_code": 401}

    def post_sdx_topology(self, event_type=None, event_timestamp=None):
        """return the topology following the SDX data model"""
        # pylint: disable=W0201
        try:
            if event_type is not None:
                converted_topology = self.convert_topology(event_type, event_timestamp)
                if converted_topology["status_code"] == 200:
                    topology_updated = converted_topology["result"]
                    self.sdx_topology = {
                        "id": topology_updated["id"],
                        "name": topology_updated["name"],
                        "version": topology_updated["version"],
                        "model_version": topology_updated["model_version"],
                        "timestamp": topology_updated["timestamp"],
                        "nodes": topology_updated["nodes"],
                        "links": topology_updated["links"],
                        "services": topology_updated["services"],
                    }
            else:
                self.sdx_topology = {}
            evaluate_topology = self.validate_sdx_topology()
            if evaluate_topology["status_code"] == 200:
                self.kytos2sdx = topology_updated.get("kytos2sdx", {})
                self.sdx2kytos = topology_updated.get("sdx2kytos", {})
                result = self.post_sdx_lc(event_type)
                return result
            log.error("Validate topology failed %s" % (evaluate_topology))
            with shelve.open("events_shelve") as log_events:
                shelve_events = log_events["events"]
                shelve_events.append(
                    {"name": "Validation error", "Error": evaluate_topology}
                )
                log_events["events"] = shelve_events
                log_events.close()
            return {
                "result": evaluate_topology["result"],
                "status_code": evaluate_topology["status_code"],
            }
        except Exception as err:  # pylint: disable=W0703
            log.info("No SDX Topology loaded, status_code 401:", err)
        return {"result": "No SDX Topology loaded", "status_code": 401}

    @listen_to(
        "kytos/topology.link_.*", "kytos/topology.switch.*", pool="dynamic_single"
    )
    def listen_event(self, event=None):
        """Function meant for listen topology"""
        if event is not None and self.version_control:
            dpid = ""
            if event.name in settings.ADMIN_EVENTS:
                switch_event = {
                    "version/control.initialize": True,
                    "kytos/topology.switch.enabled": True,
                    "kytos/topology.switch.disabled": True,
                }
                if switch_event.get(event.name, False):
                    event_type = "administrative"
                    dpid = event.content["dpid"]
                else:
                    event_type = None
            elif (
                event.name in settings.OPERATIONAL_EVENTS
                and event.timestamp is not None
            ):
                event_type = "operational"
            else:
                event_type = None
            if event_type is None:
                return {"event": "not action event"}
            # open the event shelve
            with shelve.open("events_shelve") as log_events:
                shelve_events = log_events["events"]
                shelve_events.append({"name": event.name, "dpid": dpid})
                log_events["events"] = shelve_events
                log_events.close()
            sdx_lc_response = self.post_sdx_topology(event_type, event.timestamp)
            return sdx_lc_response
        return {"event": "not action event"}

    def load_shelve(self):  # pylint: disable=W0613
        """Function meant for validation, to make sure that the store_shelve
        has been loaded before all the other functions that use it begins to
        call it."""
        if not self.shelve_loaded:  # pylint: disable=E0203
            with shelve.open("topology_shelve") as open_shelve:
                if (
                    "id" not in open_shelve.keys()
                    or "name" not in open_shelve.keys()
                    or "version" not in open_shelve.keys()
                ):
                    open_shelve["id"] = "urn:sdx:topology:" + self.oxpo_url
                    open_shelve["name"] = self.oxpo_name
                    open_shelve["url"] = self.oxpo_url
                    open_shelve["version"] = 0
                    open_shelve["model_version"] = "2.0.0"
                    open_shelve["timestamp"] = utils.get_timestamp()
                    open_shelve["nodes"] = []
                    open_shelve["links"] = []
                self.dict_shelve = dict(open_shelve)  # pylint: disable=W0201
                self.shelve_loaded = True  # pylint: disable=W0201
                open_shelve.close()
            with shelve.open("events_shelve") as events_shelve:
                events_shelve["events"] = []
                events_shelve.close()

    @rest("v1/version/control", methods=["GET"])
    def get_version_control(self, _request: Request) -> JSONResponse:
        """return true if kytos topology is ready"""
        dict_shelve = {}
        self.load_shelve()
        name = "version/control.initialize"
        content = {"dpid": ""}
        event = KytosEvent(name=name, content=content)
        self.version_control = True  # pylint: disable=W0201
        event_type = "administrative"
        sdx_lc_response = self.post_sdx_topology(event_type, event.timestamp)
        if sdx_lc_response["status_code"]:
            if sdx_lc_response["status_code"] == 200:
                if sdx_lc_response["result"]:
                    result = sdx_lc_response["result"]
                    with shelve.open("topology_shelve") as open_shelve:
                        open_shelve["version"] = 1
                        self.version_control = True  # pylint: disable=W0201
                        open_shelve["timestamp"] = result["timestamp"]
                        open_shelve["nodes"] = result["nodes"]
                        open_shelve["links"] = result["links"]
                        dict_shelve = dict(open_shelve)
                        open_shelve.close()
                    with shelve.open("events_shelve") as log_events:
                        shelve_events = log_events["events"]
                        shelve_events.append({"name": event.name, "dpid": ""})
                        log_events["events"] = shelve_events
                        log_events.close()
        return JSONResponse(dict_shelve)

    @rest("v1/topology", methods=["GET"])
    def get_topology(self, _request: Request) -> JSONResponse:
        """return sdx topology"""
        return JSONResponse(self.sdx_topology)

    @rest("v1/shelve/topology", methods=["GET"])
    def get_shelve_topology(self, _request: Request) -> JSONResponse:
        """return sdx topology shelve"""
        open_shelve = shelve.open("topology_shelve")
        dict_shelve = dict(open_shelve)
        dict_shelve["version_control"] = self.version_control
        open_shelve.close()
        return JSONResponse(dict_shelve)

    @rest("v1/shelve/events", methods=["GET"])
    def get_shelve_events(self, _request: Request) -> JSONResponse:
        """return events shelve"""
        with shelve.open("events_shelve") as open_shelve:
            events = open_shelve["events"]
        open_shelve.close()
        return JSONResponse({"events": events})

    @rest("v1/l2vpn_ptp", methods=["POST"])
    def create_l2vpn_ptp(self, request: Request) -> JSONResponse:
        """REST to create L2VPN ptp connection."""
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
            kytos_evc_url = os.environ.get("KYTOS_EVC_URL", settings.KYTOS_EVC_URL)
            response = requests.post(kytos_evc_url, json=evc_dict, timeout=30)
            assert response.status_code == 201, response.text
        except requests.exceptions.Timeout as exc:
            log.warn("EVC creation failed timout on Kytos: %s", exc)
            raise HTTPException(400, detail=f"Request to Kytos timeout: {exc}") from exc
        except AssertionError as exc:
            log.warn("EVC creation failed on Kytos: %s", exc)
            raise HTTPException(400, detail=f"Request to Kytos failed: {exc}") from exc
        except Exception as exc:
            log.warn("EVC creation failed on Kytos request: %s", exc)
            raise HTTPException(400, detail=f"Request to Kytos failed: {exc}") from exc

        return JSONResponse(response.json(), 200)
