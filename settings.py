"""Module with the Constants used in the kytos/sdx."""

EVENT_TYPES = {
    "kytos/topology.switch.enabled": "admin",
    "kytos/topology.switch.disabled": "admin",
    "kytos/topology.switch.deleted": "admin",
    "kytos/topology.link.enabled": "admin",
    "kytos/topology.link.disabled": "admin",
    "kytos/topology.link.deleted": "admin",
    "kytos/topology.link_up": "oper",
    "kytos/topology.link_down": "oper",
    "kytos/of_core.switch.interface.created": "admin",
    "kytos/of_core.switch.interface.deleted": "admin",
    "kytos/of_core.switch.interface.link_up": "oper",
    "kytos/of_core.switch.interface.link_down": "oper",
}

# Kytos mef_eline endpoint for creating L2VPN PTP
KYTOS_EVC_URL = "http://127.0.0.1:8181/api/kytos/mef_eline/v2/evc/"

# Kytos topology API
KYTOS_TOPOLOGY_URL = "http://127.0.0.1:8181/api/kytos/topology/v3/"

# Kytos topology endpoint for obtaining vlan tags
KYTOS_TAGS_URL = "http://127.0.0.1:8181/api/kytos/topology/v3/interfaces/tag_ranges"
