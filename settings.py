"""Module with the Constants used in the kytos/sdx."""

# SDXLC_URL: URL to send the topology to SDX-LC
# you can change the value below or override it using environment variable
SDXLC_URL = "http://127.0.0.1:8080/SDX-LC/2.0.0/topology"

# OXPO_NAME: Open Exchange Point Name
# you can change the value below or override it using environment variable
OXPO_NAME = "TestOXP"

# OXPO_URL: OXP URL
# you can change the value below or override it using environment variable
OXPO_URL = "testoxp.net"

# TOPOLOGY_EVENT_WAIT: time to wait while hanlde topology update
# events to try to group them
TOPOLOGY_EVENT_WAIT = 5

# Kytos mef_eline endpoint for creating L2VPN PTP
KYTOS_EVC_URL = "http://127.0.0.1:8181/api/kytos/mef_eline/v2/evc/"

# Kytos topology API
KYTOS_TOPOLOGY_URL = "http://127.0.0.1:8181/api/kytos/topology/v3/"

# Kytos topology endpoint for obtaining vlan tags
KYTOS_TAGS_URL = "http://127.0.0.1:8181/api/kytos/topology/v3/interfaces/tag_ranges"

# NAME_PREFIX: string to be prefixed on EVCs names
NAME_PREFIX = "SDX-L2VPN-"

# SDX_DEF_INCLUDE: Define if components of the topology should be exported to SDX
# by default: Switches, Interfaces and Links. If set to True (default value), then
# all items of the topology will be exported, unless the item has an specific metadata
# attribute saying the opposite
SDX_DEF_INCLUDE = {"switch": True, "interface": True, "link": True}

# Override interface vlan range for sdx when no sdx_vlan_range metadata
# is available. None means it wont override, it will defaults to interface
# tag_ranges. Example:
# OVERRIDE_VLAN_RANGE = [[100, 200]]
OVERRIDE_VLAN_RANGE = None
