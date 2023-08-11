"""
Main module of amlight/sdx Kytos Network Application.
"""
import os
import shelve
import requests
from napps.kytos.sdx_topology.convert_topology import (
        ParseConvertTopology)  # pylint: disable=E0401
from napps.kytos.sdx_topology import settings, utils, topology_mock \
        # pylint: disable=E0401

from kytos.core import KytosNApp, log, rest
from kytos.core.events import KytosEvent
from kytos.core.helpers import listen_to
from kytos.core.rest_api import (HTTPException, JSONResponse, Request,
                                 content_type_json_or_415, get_json_or_400)

HSH = "##########"
URN = "urn:sdx:"


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
        log.debug(f"{HSH}{HSH}{HSH}")
        log.debug(f"{HSH}sdx topology{HSH}")
        log.debug(f"{HSH}{HSH}{HSH}")
        self.event_info = {}  # pylint: disable=W0201
        self.sdx_topology = {}  # pylint: disable=W0201
        self.shelve_loaded = False  # pylint: disable=W0201

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

    def test_kytos_topology(self):
        """ Test if the Topology napp has loaded """
        try:
            _ = self.get_kytos_topology()
            return True
        except Exception as err:  # pylint: disable=W0703
            log.debug(err)
            return False

    @staticmethod
    def get_kytos_topology():
        """retrieve topology from API"""
        kytos_topology = requests.get(
                settings.KYTOS_TOPOLOGY, timeout=10).json()
        return kytos_topology["topology"]

    def validate_sdx_topology(self):
        """ return 200 if validated topology following the SDX data model"""
        f_name = " validate_sdx_topology "
        log.info(f"{HSH}{HSH}{HSH}{HSH}{HSH}")
        log.info(f"{HSH}{f_name}{HSH}")
        log.info(f"{HSH}{HSH}{HSH}{HSH}{HSH}")
        log.info(f"{HSH} sdx_topology: {self.sdx_topology}{HSH}")
        log.info(f"{HSH}{HSH}{HSH}{HSH}{HSH}")
        try:
            response = requests.post(
                    settings.SDX_TOPOLOGY_VALIDATE,
                    json=self.sdx_topology,
                    timeout=10)
        except ValueError as exception:
            log.info("validate topology result %s %s", exception, 401)
            raise HTTPException(
                    401,
                    detail=f"Path is not valid: {exception}"
                ) from exception
        log.info(f"{HSH}{HSH}{HSH}{HSH}{HSH}")
        log.info(f"{HSH} validate_sdx_topology response: {response}{HSH}")
        log.info(f"{HSH} validate_sdx_topology response.json: \
                {response.json()}{HSH}")
        log.info(f"{HSH} validate_sdx_topology response.status: \
                {response.status_code}{HSH}")
        log.info(f"{HSH}{HSH}{HSH}{HSH}{HSH}")
        return {"result": response.json(), "status_code": response.status_code}

    def convert_topology(self, event_type=0, event_timestamp=None):
        """Function that will take care of update the shelve containing
        the version control that will be updated every time a change is
        detected in kytos topology, and return a new sdx topology"""
        try:
            # open the topology shelve
            with shelve.open("topology_shelve") as open_shelve:
                version = open_shelve['version']
                self.dict_shelve = dict(open_shelve)  # pylint: disable=W0201
                open_shelve.close()
            if version >= 1 and event_type != 0:
                timestamp = utils.get_timestamp()
                if event_type == 1:
                    version += 1
                elif event_type == 2:
                    timestamp = event_timestamp
                return ParseConvertTopology(
                    topology=self.get_kytos_topology(),
                    version=version,
                    timestamp=timestamp,
                    model_version=self.dict_shelve['model_version'],
                    oxp_name=self.dict_shelve['oxp_name'],
                    oxp_url=self.dict_shelve['oxp_url'],
                ).parse_convert_topology()
            return {"result": topology_mock.topology_mock(),
                    "status_code": 200}
        except Exception as err:  # pylint: disable=W0703
            log.info(err)
            return {"result": "Validation Error", "status_code": 400}

    def post_sdx_lc(self, event_type):
        """ return the status from post sdx topology to sdx lc"""
        log.info(f"{HSH}{HSH}{HSH}{HSH}{HSH}")
        f_name = " post_sdx_lc response "
        log.info(f"{HSH}{f_name}{HSH}")
        post_topology = requests.post(
                settings.SDX_LC_TOPOLOGY,
                timeout=10,
                json=self.sdx_topology)
        log.info(f"{HSH}{HSH}{HSH}{HSH}{HSH}")
        log.info(f"json: {post_topology.json()}")
        log.info(f"{HSH}{HSH}{HSH}{HSH}{HSH}")
        log.info(f"status: {post_topology.status_code}")
        log.info(f"{HSH}{HSH}{HSH}{HSH}{HSH}")
        if post_topology.status_code == 200:
            if event_type != 0:
                # open the topology shelve
                with shelve.open("topology_shelve") as open_shelve:
                    open_shelve['version'] = self.sdx_topology["version"]
                    open_shelve['timestamp'] = self.sdx_topology["timestamp"]
                    open_shelve['nodes'] = self.sdx_topology["nodes"]
                    open_shelve['links'] = self.sdx_topology["links"]
                    # now, we simply close the shelf file.
                    open_shelve.close()
            log.info(f"{HSH}{HSH}{HSH}{HSH}{HSH}")
            f_name = " post_sdx_topology return sdx_topology 200 "
            log.info(f"{HSH}{f_name}{HSH}")
            return {"result": self.sdx_topology,
                    "status_code": post_topology.status_code}
        log.info(f"{HSH}{HSH}{HSH}{HSH}{HSH}")
        f_name = " post_sdx_topology return post_topology 400 "
        log.info(f"{HSH}{f_name}{HSH}")
        return {"result": post_topology.json(),
                "status_code": post_topology.status_code}

    def post_sdx_topology(self, event_type=0, event_timestamp=None):
        """ return the topology following the SDX data model"""
        # pylint: disable=W0201
        f_name = " post_sdx_topology "
        log.info(f"{HSH}{HSH}{HSH}{HSH}{HSH}")
        log.info(f"{HSH}{f_name}{HSH}")
        log.info(f"{HSH}{HSH}{HSH}{HSH}{HSH}")
        try:
            if event_type != 0:
                topology_update = self.convert_topology(
                        event_type, event_timestamp)
                self.sdx_topology = {
                        "id": topology_update["id"],
                        "name": topology_update["name"],
                        "version": topology_update["version"],
                        "model_version": topology_update["model_version"],
                        "timestamp": topology_update["timestamp"],
                        "nodes": topology_update["nodes"],
                        "links": topology_update["links"],
                        }
            else:
                self.sdx_topology = topology_mock.topology_mock()
            evaluate_topology = self.validate_sdx_topology()
            if evaluate_topology["status_code"] == 200:
                result = self.post_sdx_lc(event_type)
                log.info(f"{HSH}{HSH}{HSH}{HSH}{HSH}")
                f_name = " post_sdx_topology result "
                log.info(f"{HSH}{f_name}{HSH}")
                log.info(f"{HSH}{result}{HSH}")
                return result
            log.info(f"{HSH}{HSH}{HSH}{HSH}{HSH}")
            f_name = " post_sdx_topology return post_topology not valid "
            log.info(f"{HSH}{f_name}{HSH}")
            return {"result": evaluate_topology['result'],
                    "status_code": evaluate_topology['status_code']}
        except Exception as err:  # pylint: disable=W0703
            log.info(err)
        return {"result": "No SDX Topology loaded", "status_code": 401}

    @listen_to("kytos/topology.*")
    def listen_event(self, event=None):
        """Function meant for listen topology"""
        f_name = " listen_event "
        log.info(f"{HSH}{HSH}{HSH}{HSH}{HSH}")
        log.info(f"{HSH}{f_name} {HSH}")
        log.info(f"{HSH} dir(event): {dir(event)} {HSH}")
        log.info(f"{HSH} event: {event} {HSH}")
        log.info(f"{HSH} event.name: {event.name} {HSH}")
        log.info(f"{HSH} event.content: {event.content} {HSH}")
        log.info(f"{HSH}{HSH}{HSH}{HSH}{HSH}")
        if event is not None and self.get_kytos_topology():
            if event.name in settings.ADMIN_EVENTS:
                event_type = 1
            elif event.name in settings.OPERATIONAL_EVENTS and \
                    event.timestamp is not None:
                event_type = 2
            else:
                return {"event": "not action event"}
            # open the event shelve
            with shelve.open("events_shelve") as log_events:
                shelve_events = log_events['events']
                shelve_events.append(event.name)
                log_events['events'] = shelve_events
                log_events.close()
            return self.post_sdx_topology(event_type, event.timestamp)
        log.info(
                f"{HSH} event:{event}, topology: {self.get_kytos_topology()}")
        return {"event": event, "topology": self.get_kytos_topology()}

    def load_shelve(self):  # pylint: disable=W0613
        """Function meant for validation, to make sure that the store_shelve
        has been loaded before all the other functions that use it begins to
        call it."""
        if not self.shelve_loaded:  # pylint: disable=E0203
            # open the sdx topology shelve file
            with shelve.open("topology_shelve") as open_shelve:
                if 'id' not in open_shelve.keys() or \
                        'name' not in open_shelve.keys():
                    # initialize sdx topology
                    open_shelve['id'] = URN+"topology:"+os.environ.get(
                            "OXPO_URL")
                    open_shelve['name'] = os.environ.get("OXPO_NAME")
                    open_shelve['url'] = os.environ.get("OXPO_URL")
                    open_shelve['version'] = 0
                    open_shelve['model_version'] = os.environ.get(
                            "MODEL_VERSION")
                    open_shelve['timestamp'] = utils.get_timestamp()
                    open_shelve['nodes'] = []
                    open_shelve['links'] = []
                self.dict_shelve = dict(open_shelve)  # pylint: disable=W0201
                self.shelve_loaded = True  # pylint: disable=W0201
                # now, we simply close the shelf file.
                open_shelve.close()
            # open the events shelve file
            with shelve.open("events_shelve") as events_shelve:
                events_shelve['events'] = []
                events_shelve.close()

    # rest api tests

    @rest("v1/validate_sdx_topology", methods=["POST"])
    def get_validate_sdx_topology(self, request: Request) -> JSONResponse:
        """ REST to return the validated sdx topology status"""
        # pylint: disable=W0201
        f_name = " get_validate_sdx_topology "
        log.info(f"{HSH}{HSH}{HSH}{HSH}{HSH}")
        log.info(f"{HSH}{f_name}{HSH}")
        log.info(f"request: {request}")
        log.info(f"{HSH}{HSH}{HSH}{HSH}{HSH}")
        content = get_json_or_400(request, self.controller.loop)
        self.sdx_topology = content.get("sdx_topology")
        f_name = " get_json_or_400: "
        log.info(f"{HSH}{HSH}{HSH}{HSH}{HSH}")
        log.info(f"{HSH}{f_name} content: {content} \
                sdx_topology: {self.sdx_topology} {HSH}")
        log.info(f"{HSH}{HSH}{HSH}{HSH}{HSH}")
        if self.sdx_topology is None:
            self.sdx_topology = topology_mock.topology_mock()
            f_name = " sdx_topology is None "
            log.info(f"{HSH}{HSH}{HSH}{HSH}{HSH}")
            log.info(f"{HSH}{f_name}{HSH}")
            # log.info(f"sdx_topology: {sdx_topology}")
            log.info(f"{HSH}{HSH}{HSH}{HSH}{HSH}")
        response = self.validate_sdx_topology()
        result = response["result"]
        status_code = response["status_code"]
        log.info(f"{HSH}{HSH}{HSH}{HSH}{HSH}")
        f_name = " get_validate_sdx_topology response "
        log.info(f"{HSH}{f_name}{HSH}")
        log.info(f"response: {response}")
        log.info(f"result: {result}")
        log.info(f"status: {status_code}")
        log.info(f"{HSH}{HSH}{HSH}{HSH}{HSH}")
        return JSONResponse(result, status_code)

    @rest("v1/convert_topology/{event_type}/{event_timestamp}")
    def get_converted_topology(self, request: Request) -> JSONResponse:
        """ REST to return the converted sdx topology"""
        f_name = " get_convert_topology "
        log.info(f"{HSH}{HSH}{HSH}{HSH}{HSH}")
        log.info(f"{HSH}{f_name}{HSH}")
        log.info(f"{HSH}{HSH}{HSH}{HSH}{HSH}")
        event_type = request.path_params["event_type"]
        event_timestamp = request.path_params["event_timestamp"]
        log.info(f"{HSH}event_type: {event_type}{HSH}")
        log.info(f"{HSH}event_timestamp: {event_timestamp}{HSH}")
        log.info(f"{HSH}{HSH}{HSH}{HSH}{HSH}")
        response = self.convert_topology(event_type, event_timestamp)
        result = response["result"]
        status_code = response["status_code"]
        log.info(f"{HSH}{HSH}{HSH}{HSH}{HSH}")
        f_name = " get_converted_topology response "
        log.info(f"{HSH}{f_name}{HSH}")
        log.info(f"response: {response}")
        log.info(f"result: {result}")
        log.info(f"status: {status_code}")
        log.info(f"{HSH}{HSH}{HSH}{HSH}{HSH}")
        return JSONResponse(result, status_code)

    @rest("v1/post_sdx_topology/{event_type}/{event_timestamp}")
    def get_sdx_topology(self, request: Request) -> JSONResponse:
        """ REST to return the sdx topology loaded"""
        f_name = " get_sdx_topology "
        log.info(f"{HSH}{HSH}{HSH}{HSH}{HSH}")
        log.info(f"{HSH}{f_name}{HSH}")
        log.info(f"{HSH}path_params: {request.path_params}{HSH}")
        log.info(f"{HSH}{HSH}{HSH}{HSH}{HSH}")
        event_type = request.path_params["event_type"]
        event_timestamp = request.path_params["event_timestamp"]
        log.info(f"{HSH}event_type: {event_type}{HSH}")
        log.info(f"{HSH}event_timestamp: {event_timestamp}{HSH}")
        log.info(f"{HSH}{HSH}{HSH}{HSH}{HSH}")
        response = self.post_sdx_topology(event_type, event_timestamp)
        result = response["result"]
        status_code = response["status_code"]
        log.info(f"{HSH}{HSH}{HSH}{HSH}{HSH}")
        f_name = " get_sdx_topology response "
        log.info(f"{HSH}{f_name}{HSH}")
        log.info(f"response: {response}")
        log.info(f"result: {result}")
        log.info(f"status: {status_code}")
        log.info(f"{HSH}{HSH}{HSH}{HSH}{HSH}")
        return JSONResponse(result, status_code)

    @rest("v1/listen_event", methods=["POST"])
    def get_listen_event(self, request: Request) -> JSONResponse:
        """consume call listen Event"""
        f_name = " get_listen_event "
        log.info(f"{HSH}{f_name}{HSH}")
        try:
            result = get_json_or_400(request, self.controller.loop)
            name = result.get("name")
            content = result.get("content")
            event = KytosEvent(
                    name=name, content=content)
            # self.controller.buffers.app.put(event)
            sdx_topology = self.listen_event(event)
            return JSONResponse({"sdx_topology": sdx_topology})
        except requests.exceptions.HTTPError as http_error:
            raise SystemExit(
                    http_error, detail="listen topology fails") from http_error

    @rest("v1/shelve/topology", methods=["GET"])
    def get_shelve_topology(self, _request: Request) -> JSONResponse:
        """return sdx topology shelve"""
        open_shelve = shelve.open("topology_shelve")
        dict_shelve = dict(open_shelve)
        open_shelve.close()
        return JSONResponse(dict_shelve)

    @rest("v1/shelve/events", methods=["GET"])
    def get_shelve_events(self, _request: Request) -> JSONResponse:
        """return events shelve"""
        f_name = " get_shelve_events "
        log.info(f"{HSH}{f_name}{HSH}")
        with shelve.open("events_shelve") as open_shelve:
            events = open_shelve['events']
        open_shelve.close()
        return JSONResponse({"events": events})
