"""Module to help to create tests."""

import json
from pathlib import Path
from unittest.mock import MagicMock

from kytos.core.interface import Interface
from kytos.core.link import Link
from kytos.core.switch import Switch


def get_topology_dict():
    """Get the topology dict."""
    return json.loads((Path(__file__).parent / "test_topo.json").read_text())[
        "topology"
    ]


def get_topology():
    """Create a default topology."""
    switches = {}
    links = {}
    interfaces = {}
    topo = get_topology_dict()

    for key, value in topo["switches"].items():
        switch = Switch(key)
        switch.enable()
        switch.is_active = MagicMock(return_value=value["active"])
        switch.metadata = value["metadata"]
        switch.description["data_path"] = value["data_path"]
        switches[key] = switch

        for intf_id, intf in value["interfaces"].items():
            interface = Interface(
                intf["name"], intf["port_number"], switch, speed=intf["speed"]
            )
            interface.enable()
            interface.metadata = intf["metadata"]
            switch.interfaces[intf_id] = interface
            interfaces[intf_id] = interface

    for key, value in topo["links"].items():
        intf1 = interfaces[value["endpoint_a"]["id"]]
        intf2 = interfaces[value["endpoint_b"]["id"]]
        link = Link(intf1, intf2)
        link.enable()
        link.metadata = value["metadata"]
        intf1.update_link(link)
        intf2.update_link(link)
        intf1.nni = True
        intf2.nni = True
        links[key] = link

    topology = MagicMock()
    topology.links = links
    topology.switches = switches

    return topology


def get_converted_topology():
    """Get the converted topology."""
    return json.loads((Path(__file__).parent / "test_topo_converted.json").read_text())


def get_evc():
    """Get EVC from Kytos."""
    return json.loads((Path(__file__).parent / "test_evc.json").read_text())


def get_evc_converted():
    """Get EVC from Kytos."""
    return json.loads((Path(__file__).parent / "test_evc_converted.json").read_text())
