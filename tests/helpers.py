"""Module to help to create tests."""

import json
from unittest.mock import MagicMock
from pathlib import Path

from kytos.core.interface import Interface
from kytos.core.link import Link
from kytos.core.switch import Switch
from kytos.lib.helpers import (get_interface_mock, get_link_mock,
                               get_switch_mock)

def get_topology():
    """Create a default topology."""
    switches = {}
    links = {}
    interfaces = {}
    topo = json.loads((Path(__file__).parent / "test_topo.json").read_text())

    for key, value in topo["topology"]["switches"].items():
        switch = Switch(key)
        switch.enable()
        #switch.id = key
        switch.is_active = MagicMock(return_value = value["active"])
        #switch.is_enabled.return_value = value["enabled"]
        switch.metadata = value["metadata"]
        switch.description["data_path"] = value["data_path"]
        #switch.as_dict.return_value = value
        #switch.interfaces = {}
        switches[key] = switch

        for intf_id, intf in value["interfaces"].items():
            interface = Interface(intf["name"], intf["port_number"], switch, speed=intf["speed"])
            interface.enable()
            #interface.id = intf_id
            #interface.is_active.return_value = intf["active"]
            #interface.is_enabled.return_value = intf["enabled"]
            interface.metadata = intf["metadata"]
            #interface.as_dict.return_value = intf
            switch.interfaces[intf_id] = interface
            interfaces[intf_id] = interface

    for key, value in topo["topology"]["links"].items():
        intf1 = interfaces[value["endpoint_a"]["id"]]
        intf2 = interfaces[value["endpoint_b"]["id"]]
        link = Link(intf1, intf2)
        link.enable()
        #link.id = key
        #link.is_active.return_value = value["active"]
        #link.is_enabled.return_value = value["enabled"]
        link.metadata = value["metadata"]
        intf1.update_link(link)
        intf2.update_link(link)
        intf1.nni = True
        intf2.nni = True
        #link.as_dict.return_value = value
        links[key] = link

    topology = MagicMock()
    topology.links = links
    topology.switches = switches

    return topology

def get_converted_topology():
    """Get the converted topology."""
    return json.loads(
        (Path(__file__).parent / "test_topo_converted.json").read_text()
    )
