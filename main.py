"""
Main module of kytos/sdx_topology Kytos Network Application.

SDX API
"""

import requests
from flask import jsonify, request

from kytos.core import KytosNApp, log, rest
from kytos.core.helpers import listen_to
from napps.kytos.sdx_topology import settings, storehouse \
        # pylint: disable=E0401
from napps.kytos.sdx_topology.topology_class import ParseTopology \
        # pylint: disable=E0401
from napps.kytos.sdx_topology.utils import load_spec, validate \
        # pylint: disable=E0401


class Main(KytosNApp):
    """Main class of kytos/sdx_topology NApp.

    This class is the entry point for this NApp.
    """

    spec = load_spec()

    def setup(self):
        """Replace the '__init__' method for the KytosNApp subclass.

        The setup method is automatically called by the controller when your
        application is loaded.

        So, if you have any setup routine, insert it here.
        """
        self.topology_loaded = False
        self.storehouse = None
        self.valid_sdx = None

    def execute(self):
        """Run after the setup method execution.

        You can also use this method in loop mode if you add to the above setup
        method a line like the following example:

            self.execute_as_loop(30)  # 30-second interval.
        """
        self.load_storehouse()

    def shutdown(self):
        """Run when your NApp is unloaded.

        If you have some cleanup procedure, insert it here.
        """

    @property
    def oxp_url(self):
        """ Property for OXP_URL """
        if self.load_storehouse():
            return self.storehouse.get_data()["oxp_url"]
        return ""

    @oxp_url.setter
    def oxp_url(self, oxp_url):
        """ Property for OXP_URL """
        self.storehouse.save_oxp_url(oxp_url)

    @property
    def oxp_name(self):
        """ Property for OXP_NAME """
        if self.load_storehouse():
            return self.storehouse.get_data()["oxp_name"]
        return ""

    @oxp_name.setter
    def oxp_name(self, oxp_name):
        """ Property for OXP_URL """
        self.storehouse.save_oxp_name(oxp_name)

    @listen_to("kytos/storehouse.loaded")
    def load_storehouse(self, event=None):  # pylint: disable=W0613
        """Function meant for validation, to make sure that the storehouse \
                napp has been loaded before all the other functions that use \
                it begins to call it."""
        log.info("Loading Storehouse")
        self.storehouse = storehouse.StoreHouse(self.controller)  \
            # pylint: disable=W0201

    @listen_to("kytos/topology.*")
    def load_topology(self, event=None):  # pylint: disable=W0613
        """Function meant for validation, to make sure that the storehouse \
                napp has been loaded before all the other functions that use \
                it begins to call it."""
        if not self.topology_loaded:
            if self.storehouse:
                if self.storehouse.box is not None:
                    self.create_update_topology()
                    self.topology_loaded = True  # pylint: disable=W0201
            else:
                self.topology_loaded = True  # pylint: disable=W0201

    @listen_to("kytos/topology.unloaded")
    def unload_topology(self):  # pylint: disable=W0613
        """Function meant for validation, to make sure that the storehouse napp
        has been loaded before all the other functions that use it begins to
        call it."""
        self.topology_loaded = False  # pylint: disable=W0201

    def test_kytos_topology(self):
        """ Test if the Topology napp has loaded """
        if "_" == self.get_kytos_topology():
            return True
        return False

    @staticmethod
    def get_kytos_topology():
        """retrieve topology from API"""
        kytos_topology = requests.get(settings.KYTOS_TOPOLOGY_URL).json()
        return kytos_topology["topology"]

    @rest("v1/oxp_url", methods=["GET"])
    def get_oxp_url(self):
        """ REST endpoint to RETRIEVE the SDX napp oxp_url"""
        return jsonify(self.oxp_url), 200

    @rest("v1/oxp_url", methods=["POST"])
    def set_oxp_url(self):
        """ REST endpoint to provide the SDX napp with the url provided \
                by the operator"""
        try:
            self.oxp_url = request.get_json()

        except Exception as err:  # pylint: disable=W0703
            log.info(err)
            return jsonify(err), 401

        if not isinstance(self.oxp_url, str):
            return jsonify("Incorrect Type submitted"), 401

        return jsonify(self.oxp_url), 200

    @rest("v1/oxp_name", methods=["GET"])
    def get_oxp_name(self):
        """ REST endpoint to RETRIEVE the SDX napp domain_name"""
        return jsonify(self.oxp_name), 200

    @rest("v1/oxp_name", methods=["POST"])
    def set_oxp_name(self):
        """ REST endpoint to provide the SDX napp with the domain_name \
                provided by the operator"""
        try:
            self.oxp_name = request.get_json()

        except Exception as err:  # pylint: disable=W0703
            log.info(err)
            return jsonify(err), 401

        if not isinstance(self.oxp_name, str):
            return jsonify("Incorrect Type submitted"), 401

        return jsonify(self.oxp_name), 200

    @rest("v1/validate", methods=["POST"])
    @validate(spec)
    def validate_topology(self):
        """ Return the valid sdx topology following the SDX data model"""
        self.oxp_validate = request.get_json()

    @rest("v1/topology")
    def get_topology_version(self):
        """ REST to return the topology following the SDX data model"""
        if not self.oxp_url:
            return jsonify(
                    "Submit oxp_url previous to requesting topology schema"),\
                            401
        if not self.oxp_name:
            return (
                jsonify(
                    "Submit oxp_name previous to requesting topology schema"),
                401,
            )
        if self.topology_loaded or self.test_kytos_topology():
            topology_update = self.create_update_topology()
            topology_dict = {
                "id": topology_update["id"],
                "name": topology_update["name"],
                "version": topology_update["version"],
                "model_version": topology_update["model_version"],
                "timestamp": topology_update["timestamp"],
                "nodes": topology_update["nodes"],
                "links": topology_update["links"],
            }
            validate_topology = requests.post(
                settings.VALIDATE_TOPOLOGY, json=topology_dict
            )
            if validate_topology.status_code == 200:
                return jsonify(topology_update), 200
            return jsonify(validate_topology.json()), 400
        # debug only
        log.info(self.topology_loaded)
        log.info(self.test_kytos_topology())
        return jsonify("Topology napp has not loaded"), 401

    def create_update_topology(self):
        """Function that will take care of initializing the namespace
        kytos.storehouse.version within the storehouse and create a
        box object containing the version data that will be updated
        every time a change is detected in the topology."""
        self.storehouse.update_box()
        parse_args = {
            "topology": self.get_kytos_topology(),
            "version": self.storehouse.get_data()["version"],
            "model_version": "1.0.0",
            "oxp_name": self.oxp_name,
            "oxp_url": self.oxp_url
        }
        return ParseTopology(parse_args).get_sdx_topology()