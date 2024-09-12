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
TOPOLOGY_EVENT_WAIT=5

# Kytos mef_eline endpoint for creating L2VPN PTP
KYTOS_EVC_URL = "http://127.0.0.1:8181/api/kytos/mef_eline/v2/evc/"

# Kytos topology API
KYTOS_TOPOLOGY_URL = "http://127.0.0.1:8181/api/kytos/topology/v3/"

# Kytos topology endpoint for obtaining vlan tags
KYTOS_TAGS_URL = "http://127.0.0.1:8181/api/kytos/topology/v3/interfaces/tag_ranges"
