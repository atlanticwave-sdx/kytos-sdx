"""Module with the Constants used in the kytos/sdx_topology."""

HEADERS = {"Content-type": "application/json"}
ADMIN_EVENTS = [
        "version/control.initialize",
        "kytos/topology.switch.enabled",
        "kytos/topology.switch.disabled",
        "kytos/topology.switch.metadata.added",
        "kytos/topology.interface.metadata.added",
        "kytos/topology.link.metadata.added",
        "kytos/topology.switch.metadata.removed",
        "kytos/topology.interface.metadata.removed",
        "kytos/topology.link.metadata.removed",
        # 'kytos/topology.notify_link_up_if_status',
        # 'kytos/core.shutdown',
        # 'kytos/core.shutdown.kytos/topology',
        # '.*.topo_controller.upsert_switch',
        # '.*.of_lldp.network_status.updated',
        # '.*.switch.interfaces.created',
        # '.*.topology.switch.interface.created',
        # '.*.switch.interface.deleted',
        # '.*.switch.port.created',
        # 'topology.interruption.start',
        # 'topology.interruption.end',
        ]
OPERATIONAL_EVENTS = [
        "topology_loaded",
        "kytos/topology.link_up",
        "kytos/topology.link_down",
        # '.*.connection.lost',
        # '.*.switch.interface.link_down',
        # '.*.switch.interface.link_up',
        # '.*.switch.(new|reconnected)'
        ]

# Kytos mef_eline endpoint for creating L2VPN PTP
KYTOS_EVC_URL = "http://127.0.0.1:8181/api/kytos/mef_eline/v2/evc/"

# Kytos topology API
KYTOS_TOPOLOGY_URL = "http://127.0.0.1:8181/api/kytos/topology/v3/"
