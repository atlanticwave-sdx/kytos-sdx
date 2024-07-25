"""
Main class of kytos/sdx_topology Kytos Network Application.

SDX API
"""


class ParseConvertTopology:
    """Parse Topology  class of kytos/sdx_topology NApp."""

    def __init__(self, **args):
        self.kytos_topology = args["topology"]
        self.version = args["version"]
        self.timestamp = args["timestamp"]
        self.oxp_name = args["oxp_name"]
        self.oxp_url = args["oxp_url"]
        self.model_version = "2.0.0"
        # mapping from Kytos to SDX and vice-versa
        self.kytos2sdx = {}
        self.sdx2kytos = {}

    def get_kytos_nodes(self) -> dict:
        """return parse_args["topology"]["switches"] values"""
        return self.kytos_topology["switches"].values()

    def get_kytos_links(self) -> dict:
        """return parse_args["topology"]["links"] values"""
        return self.kytos_topology["links"].values()

    @staticmethod
    def get_link_port_speed(speed: str) -> int:
        """Function to obtain the speed of a specific port in the link."""
        type_to_speed = {
            "400GE": 400,
            "100GE": 100,
            "50GE": 50,
            "40GE": 40,
            "25GE": 25,
            "10GE": 10,
            "50000000000": 400,
            "50000000000.0": 400,
            "12500000000": 100,
            "12500000000.0": 100,
            "6250000000": 50,
            "6250000000.0": 50,
            "5000000000": 40,
            "5000000000.0": 40,
            "3125000000": 25,
            "3125000000.0": 25,
            "1250000000": 10,
            "1250000000.0": 10,
        }

        return type_to_speed.get(speed, 0)

    @staticmethod
    def get_type_port_speed(speed: str) -> str:
        """Function to obtain the speed of a specific port type."""
        speed_to_type = {
            "400GE": "400GE",
            "50000000000": "400GE",
            "50000000000.0": "400GE",
            "100GE": "100GE",
            "12500000000": "100GE",
            "12500000000.0": "100GE",
            "50GE": "50GE",
            "6250000000": "50GE",
            "6250000000.0": "50GE",
            "40GE": "40GE",
            "5000000000": "40GE",
            "5000000000.0": "40GE",
            "25GE": "25GE",
            "3125000000": "25GE",
            "3125000000.0": "25GE",
            "10GE": "10GE",
            "1250000000": "10GE",
            "1250000000.0": "10GE",
        }

        return speed_to_type.get(speed, "Other")

    @staticmethod
    def get_status(status: bool) -> str:
        """Function to obtain the status."""
        return "up" if status else "down"

    @staticmethod
    def get_state(state: bool) -> str:
        """Function to obtain the state."""
        return "enabled" if state else "disabled"

    def get_kytos_link_label(self, kytos_link: dict) -> str:
        """Return the kytos link label"""
        if "endpoint_a" not in kytos_link or "endpoint_b" not in kytos_link:
            raise ValueError(f"Invalid Kytos link: {kytos_link}")
        link_name = kytos_link["metadata"].get("link_name")
        if link_name:
            link_name = re.sub(r'\s+', '_', link_name)
            link_name = re.sub('[^A-Za-z0-9_.,/-]', '', link_name)
            return link_name[:30]
        interface_a = int(kytos_link["endpoint_a"]["id"][24:])
        switch_a = kytos_link["endpoint_a"]["id"][:23]
        interface_b = int(kytos_link["endpoint_b"]["id"][24:])
        switch_b = kytos_link["endpoint_b"]["id"][:23]
        node_swa = self.get_kytos_node_name(switch_a)
        node_swb = self.get_kytos_node_name(switch_b)
        return f"{node_swa}/{interface_a}_{node_swb}/{interface_b}"

    def get_port_urn(self, interface: dict) -> str:
        """function to generate the full urn address for a node"""
        switch_name = self.get_kytos_node_name(interface["switch"])
        port_no = interface["port_number"]

        return f"urn:sdx:port:{self.oxp_url}:{switch_name}:{port_no}"

    def get_port(self, sdx_node_name: str, interface: dict) -> dict:
        """Function to retrieve a network device's port (or interface)"""

        sdx_port = {}
        sdx_port["id"] = self.get_port_urn(interface)
        sdx_port["name"] = interface["metadata"].get("port_name", "")[:30]
        if not sdx_port["name"]:
            sdx_port["name"] = interface["name"][:30]
        sdx_port["node"] = f"urn:sdx:node:{self.oxp_url}:{sdx_node_name}"
        sdx_port["type"] = self.get_type_port_speed(str(interface["speed"]))
        sdx_port["status"] = self.get_status(interface["active"])
        sdx_port["state"] = self.get_state(interface["enabled"])

        sdx_port["mtu"] = interface["metadata"].get("mtu", 1500)

        if interface["nni"]:
            link_label = self.get_kytos_link_label(
                self.kytos_topology["links"].get(interface["link"])
            )
            sdx_port["nni"] = f"urn:sdx:link:{self.oxp_url}:{link_label}"
        elif "sdx_nni" in interface["metadata"]:
            sdx_port["nni"] = "urn:sdx:port:" + interface["metadata"]["sdx_nni"]
        else:
            sdx_port["nni"] = ""

        vlan_range = interface["metadata"].get("sdx_vlan_range")
        if not vlan_range:
            vlan_range = interface.get("tag_ranges", [[1, 4095]])

        sdx_port["services"] = {
            "l2vpn-ptp": {"vlan_range": vlan_range},
            # "l2vpn-ptmp":{"vlan_range": vlan_range}
        }

        sdx_port["private"] = ["status"]

        return sdx_port

    def get_ports(self, sdx_node_name: str, interfaces: dict) -> list:
        """Function that calls the main individual get_port function,
        to get a full list of ports from a node/ interface"""
        ports = []
        for interface in interfaces.values():
            port_no = interface["port_number"]
            if port_no != 4294967294:
                ports.append(self.get_port(sdx_node_name, interface))
                self.kytos2sdx[interface["id"]] = ports[-1]["id"]
                self.sdx2kytos[ports[-1]["id"]] = interface["id"]

        return ports

    def get_kytos_node_name(self, switch_id: str) -> str:
        """retrieve the data_path attribute for every Kytos topology switch"""
        switch = self.kytos_topology["switches"].get(switch_id)
        if not switch:
            raise ValueError(f"Switch {switch_id} not found on the topology")
        if "node_name" in switch["metadata"]:
            return switch["metadata"]["node_name"][:30]
        if len(switch["data_path"]) <= 30
            return switch["data_path"]
        return switch["dpid"].replace(":", "-")

    def get_sdx_node(self, kytos_node: dict) -> dict:
        """function that builds every Node dictionary object with all the
        necessary attributes that make a Node object; the name, id, location
        and list of ports."""
        sdx_node = {}

        if "node_name" in kytos_node["metadata"]:
            sdx_node["name"] = kytos_node["metadata"]["node_name"]
        else:
            sdx_node["name"] = kytos_node["data_path"]

        sdx_node["id"] = f"urn:sdx:node:{self.oxp_url}:{sdx_node['name']}"

        sdx_node["location"] = {
            "address": kytos_node["metadata"].get("address", ""),
            "latitude": float(kytos_node["metadata"].get("lat", 0)),
            "longitude": float(kytos_node["metadata"].get("lng", 0)),
            "iso3166_2_lvl4": kytos_node["metadata"].get("iso3166_2_lvl4", ""),
            "private": [],
        }

        sdx_node["ports"] = self.get_ports(sdx_node["name"], kytos_node["interfaces"])

        sdx_node["status"] = self.get_status(kytos_node["active"])
        sdx_node["state"] = self.get_state(kytos_node["enabled"])

        return sdx_node

    def get_sdx_nodes(self) -> list:
        """returns SDX Nodes list with every enabled Kytos node in topology"""
        sdx_nodes = []
        for kytos_node in self.get_kytos_nodes():
            if kytos_node["enabled"]:
                sdx_nodes.append(self.get_sdx_node(kytos_node))
        return sdx_nodes

    def get_sdx_link(self, kytos_link):
        """generates a dictionary object for every link in a network,
        and containing all the attributes for each link"""
        sdx_link = {}
        link_md = kytos_link["metadata"]

        sdx_link["name"] = self.get_kytos_link_label(kytos_link)
        sdx_link["id"] = f"urn:sdx:link:{self.oxp_url}:{sdx_link['name']}"
        sdx_link["ports"] = [
            self.get_port_urn(kytos_link["endpoint_a"]),
            self.get_port_urn(kytos_link["endpoint_b"]),
        ]
        sdx_link["type"] = "intra"
        sdx_link["bandwidth"] = self.get_link_port_speed(
            str(
                min(
                    kytos_link["endpoint_a"]["speed"],
                    kytos_link["endpoint_b"]["speed"],
                )
            )
        )
        sdx_link["residual_bandwidth"] = link_md.get("residual_bandwidth", 100)
        sdx_link["latency"] = link_md.get("latency", 0)
        sdx_link["packet_loss"] = link_md.get("packet_loss", 0)
        sdx_link["availability"] = link_md.get("availability", 0)
        sdx_link["status"] = self.get_status(kytos_link["active"])
        sdx_link["state"] = self.get_state(kytos_link["enabled"])
        sdx_link["private"] = ["packet_loss"]

        return sdx_link

    def get_sdx_links(self):
        """function that returns a list of Link objects based on the network's
        devices connections to each other"""

        sdx_links = []

        for kytos_link in self.get_kytos_links():
            if kytos_link["enabled"]:
                sdx_link = self.get_sdx_link(kytos_link)
                if sdx_link:
                    sdx_links.append(sdx_link)

        return sdx_links

    def parse_convert_topology(self):
        """function get_sdx_topology"""
        topology = {}
        topology["name"] = self.oxp_name
        topology["id"] = f"urn:sdx:topology:{self.oxp_url}"
        topology["version"] = self.version
        topology["timestamp"] = self.timestamp
        topology["model_version"] = self.model_version
        topology["nodes"] = self.get_sdx_nodes()
        topology["links"] = self.get_sdx_links()
        topology["services"] = ["l2vpn-ptp"]
        topology["kytos2sdx"] = self.kytos2sdx
        topology["sdx2kytos"] = self.sdx2kytos
        return topology
