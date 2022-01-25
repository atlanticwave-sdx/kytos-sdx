"""
This code was design to intentionally leave some validations to be performed
by the JSON schema validator. Therefore, not every attribute will be validated
every time.
"""

import datetime
import json
from secrets import randbelow
import requests


def get_nodes_name(kytos_topology):
    """Retrieve switches data_path attribute from Kytos's topology API"""
    #
    new_headers = {"Content-type": "application/json"}
    topology_url = "http://0.0.0.0:8181/api/kytos/topology/v3"
    response = requests.get(topology_url, headers=new_headers)
    kytos_topology = json.loads(response.content.decode("utf-8"))["topology"]
    nodes_mappings = {}
    for node in kytos_topology["switches"].values():
        if "node_name" in node["metadata"]:
            nodes_mappings[node] = node["metadata"]["node_name"]
        else:
            nodes_mappings[node] = node["data_path"]
    return nodes_mappings


def get_port_urn(switch, interface, oxp_url):
    """function to generate the full urn address for a node"""
    if not isinstance(interface, str) and not isinstance(interface, int):
        raise ValueError("Interface is not the proper type")
    if interface == "" or switch == "":
        raise ValueError("Interface and switch CANNOT be empty")
    if isinstance(interface, int) and interface <= 0:
        raise ValueError("Interface cannot be negative")
    try:
        switch_name = get_nodes_name(switch)
    except KeyError:
        switch_name = switch
    return f"urn:sdx:port:{oxp_url}:{switch_name}:{interface}"


def get_port_type(speed):
    """Function to obtain the speed of a specific port in the network."""
    speed_in = (
        ("1GE", 125000000, 125000000.0),
        ("10GE", 1250000000, 1250000000.0),
        ("25GE", 3125000000, 3125000000.0),
        ("40GE", 5000000000, 5000000000.0),
        ("50GE", 6250000000, 6250000000.0),
        ("100GE", 12500000000, 12500000000.0),
        ("400GE", 50000000000, 50000000000.0),
    )
    speed_out = ("1GE", "10GE", "25GE", "40GE", "50GE", "100GE", "400GE")
    result = [speed_out[x] for x in range(7) if speed in speed_in[x]][0]
    if not result:
        result = ["Other"]
    return result[0]


def get_port_speed(speed):
    """Function to obtain the speed of a specific port in the network."""
    speed_in = (
        ("1GE", 125000000, 125000000.0),
        ("10GE", 1250000000, 1250000000.0),
        ("25GE", 3125000000, 3125000000.0),
        ("40GE", 5000000000, 5000000000.0),
        ("50GE", 6250000000, 6250000000.0),
        ("100GE", 12500000000, 12500000000.0),
        ("400GE", 50000000000, 50000000000.0),
    )
    speed_out = (
        125000000,
        1250000000,
        3125000000,
        5000000000,
        6250000000,
        12500000000,
        50000000000,
    )
    result = [speed_out[x] for x in range(7) if speed in speed_in[x]][0]
    if not result:
        result = ["9999999999"]
    return result[0]


def get_port(node, interface, oxp_url):
    """Function to retrieve a network device's port (or interface) """
    if interface == "" or node == "":
        raise ValueError("Interface and node CANNOT be empty")
    port = {}
    port["id"] = get_port_urn(node, interface["port_number"], oxp_url)
    port["name"] = interface["name"]
    port["node"] = f"urn:sdx:node:{oxp_url}:{node}"
    port["type"] = get_port_type(interface["speed"])
    port["status"] = "up" if interface["active"] else "down"
    port["state"] = "enabled" if interface["enabled"] else "disabled"
    port["services"] = "l2vpn"
    port["nni"] = "False"

    if "nni" in interface["metadata"]:
        port["nni"] = interface["metadata"]["nni"]

    if "mtu" in interface["metadata"]:
        port["mtu"] = interface["metadata"]["mtu"]
    else:
        port["mtu"] = "1500"

    return port


def get_ports(node, interfaces, oxp_url):
    """Function that calls the main individual get_port function,
    to get a full list of ports from a node/ interface"""
    ports = []
    for interface in interfaces.values():
        port_no = interface["port_number"]
        if port_no != 4294967294:
            ports.append(get_port(node, interface, oxp_url))

    return ports


def get_node(switch, oxp_url):
    """function that builds every Node dictionary object with all the necessary
    attributes that make a Node object; the name, id, location and list of
    ports."""

    if switch == "":
        raise ValueError("Switch CANNOT be empty")

    node = {}

    if "node_name" in switch["metadata"]:
        node["name"] = switch["metadata"]["node_name"]
    else:
        node["name"] = switch["data_path"]
    node["id"] = f"urn:sdx:node:{oxp_url}:%s" % node["name"]
    node["location"] = {"address": "", "latitude": "", "longitude": ""}
    if "address" in switch["metadata"]:
        node["location"]["address"] = switch["metadata"]["address"]
    if "lat" in switch["metadata"]:
        node["location"]["latitude"] = switch["metadata"]["lat"]
    if "lng" in switch["metadata"]:
        node["location"]["longitude"] = switch["metadata"]["lng"]

    node["ports"] = get_ports(node["name"], switch["interfaces"], oxp_url)

    return node


def get_nodes(topology, oxp_url):
    """Returns a list of Nodes objects for every node in a topology"""

    if topology["switches"] == "":
        raise ValueError("Switches CANNOT be empty")

    nodes = []

    for switch in topology["switches"].values():
        if switch["enabled"]:
            node = get_node(switch, oxp_url)
            nodes.append(node)

    return nodes


def get_link(kytos_link, oxp_url):
    """function that generates a dictionary object for every link in a network,
    and containing all the attributes for each link"""

    if kytos_link == "":
        raise ValueError("Kytos_link CANNOT be empty")

    link = {}
    interface_a = int(kytos_link["endpoint_a"]["id"].split(":")[8])
    switch_a = ":".join(kytos_link["endpoint_a"]["id"].split(":")[0:8])
    interface_b = int(kytos_link["endpoint_b"]["id"].split(":")[8])
    switch_b = ":".join(kytos_link["endpoint_b"]["id"].split(":")[0:8])
    if switch_a == switch_b:
        return link

    name = f'{get_nodes_name(kytos_link)[switch_a]}{"/"}{interface_a}'
    name += f'{"_"}{get_nodes_name(kytos_link)[switch_b]}{"/"}{ interface_b}'
    link["name"] = name
    link["id"] = f"urn:sdx:link:{oxp_url}:%s" % link["name"]
    link["ports"] = [
        get_port_urn(switch_a, interface_a, oxp_url),
        get_port_urn(switch_b, interface_b, oxp_url),
    ]

    link["type"] = "intra"

    for item in [
        "bandwidth",
        "residual_bandwidth",
        "latency",
        "packet_loss",
        "availability",
    ]:
        if item in kytos_link["metadata"]:
            link[item] = kytos_link["metadata"][item]
        else:
            if item in ["bandwidth"]:
                link[item] = get_port_speed(kytos_link["endpoint_a"]["speed"])
            elif item in ["residual_bandwidth", "availability"]:
                link[item] = 100
            else:
                link[item] = 0

    link["status"] = "up" if kytos_link["endpoint_a"]["active"] else "down"
    link["state"] = (
        "enabled" if kytos_link["endpoint_a"]["enabled"] else "disabled"
    )

    return link


def get_links(kytos_links, oxp_url):
    """function that returns a list of Link objects based on the network's
    devices connections to each other"""

    if kytos_links == "":
        raise ValueError("Kytos_links CANNOT be empty")

    links = []

    for kytos_link in kytos_links.values():
        if kytos_link["enabled"]:
            link = get_link(kytos_link, oxp_url)
            if link:
                links.append(link)

    return links


def update_nni(nodes, links):
    """Iterate through links, and every time we find a link,
    we will populate the equivalent to the node's nni information"""
    for link in links:
        ports = link["ports"]
        nni_a, nni_b = ports[0], ports[1]
        node_a = nni_a.split(":")[4]
        port_a = nni_a.split(":")[5]
        node_b = nni_b.split(":")[4]
        port_b = nni_b.split(":")[5]
        for node in nodes:
            if node["name"] == node_a:
                for port in node["ports"]:
                    if port_a == port["id"].split(":")[5]:
                        port["nni"] = nni_b
            elif node["name"] == node_b:
                for port in node["ports"]:
                    if port_b == port["id"].split(":")[5]:
                        port["nni"] = nni_a


def create_inter_oxp_link_entries(oxp_url, nodes, links):
    """ Create entries for inter-oxp links """
    for node in nodes.values():
        for interface in node["interfaces"].values():
            if "nni" in interface["metadata"]:
                if oxp_url not in interface["metadata"]["nni"]:
                    # inter-domain

                    link = {}

                    if "link_name" in interface["metadata"]:
                        link["name"] = interface["metadata"]["link_name"]
                    else:
                        link["name"] = f"NO_NAME_{randbelow(100000)}"

                    link["id"] = f"urn:sdx:link:{oxp_url}:{link['name']}"

                    if "node_name" in node["metadata"]:
                        node["name"] = node["metadata"]["node_name"]
                    else:
                        node["name"] = node["data_path"]

                    port_id = get_port_urn(
                        node, interface["port_number"], oxp_url
                    )

                    link["ports"] = [port_id, interface["metadata"]["nni"]]

                    link["type"] = "inter"
                    link["bandwidth"] = get_port_speed(interface["speed"])
                    link["status"] = "up" if interface["active"] else "down"
                    link["state"] = (
                        "enabled" if interface["enabled"] else "disabled"
                    )

                    link["availability"] = 100
                    link["residual_bandwidth"] = 100
                    link["packet_loss"] = 0
                    link["latency"] = 0
                    links.append(link)
                    del link


def get_topology(kytos_topology, version, oxp_name, oxp_url):
    """Main function: return a topology dictionary by calling other functions
    with:
    name, id, nodes, time_stamp, version, domain_service, and links return"""

    if kytos_topology == "":
        raise ValueError("Kytos_topology CANNOT be empty")

    topology = {}
    topology["name"] = oxp_name
    topology["id"] = f"urn:sdx:topology:{oxp_url}"
    topology["version"] = version
    topology["timestamp"] = datetime.datetime.now().isoformat()[19]+"Z"
    topology["model_version"] = "1.0.0"
    topology["nodes"] = get_nodes(kytos_topology["switches"], oxp_url)
    topology["links"] = get_links(kytos_topology["links"], oxp_url)

    update_nni(topology["nodes"], topology["links"])

    create_inter_oxp_link_entries(
            oxp_url, topology["nodes"], topology["links"])

    return topology
