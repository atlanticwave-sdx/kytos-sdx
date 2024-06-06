""" topology mock """


def topology_mock():
    """ return json data """
    return {
            "id": "urn:sdx:topology:amlight.net",
            "name": "AmLight-OXP",
            "version": 1,
            "model_version": "2.0.0",
            "timestamp": "2023-01-23T04:56:07Z",
            "links": [
                {
                    "name": "amlight_B1B2",
                    "id": "urn:sdx:link:amlight_internal_BB",
                    "ports": [
                            "urn:sdx:port:amlight.net:B1:2",
                            "urn:sdx:port:amlight.net:B2:2",
                    ],
                    "type": "intra",
                    "bandwidth": 1250000000,
                    "residual_bandwidth": 80,
                    "latency": 25,
                    "packet_loss": 0.006255,
                    "availability": 99.5,
                    "status": "up",
                    "state": "enabled"
                },
                {
                    "name": "amlight_A1B1",
                    "id": "urn:sdx:link:amlight_internal_AB",
                    "ports": [
                            "urn:sdx:port:amlight.net:A1:1",
                            "urn:sdx:port:amlight.net:B1:3",
                    ],
                    "type": "intra",
                    "bandwidth": 1250000000,
                    "residual_bandwidth": 31,
                    "latency": 16,
                    "packet_loss": 0.0029453,
                    "availability": 99.5,
                    "status": "up",
                    "state": "enabled"
                },
                {
                    "name": "amlight_A1B2",
                    "id": "urn:sdx:link:amlight_internal_BA",
                    "ports": [
                            "urn:sdx:port:amlight.net:A1:2",
                            "urn:sdx:port:amlight.net:B2:3",
                    ],
                    "type": "intra",
                    "bandwidth": 1250000000,
                    "residual_bandwidth": 80,
                    "latency": 25,
                    "packet_loss": 0.006255,
                    "availability": 99.5,
                    "status": "up",
                    "state": "enabled"
                },
                {
                    "name": "nni_MiamiSanpaolo",
                    "id": "urn:sdx:link:nni_Miami_Sanpaolo",
                    "ports": [
                            "urn:sdx:port:amlight:B1:1",
                            "urn:sdx:port:sax:B1:1",
                    ],
                    "type": "intra",
                    "bandwidth": 1250000000,
                    "residual_bandwidth": 31,
                    "latency": 16,
                    "packet_loss": 0.0029453,
                    "availability": 99.5,
                    "status": "up",
                    "state": "enabled"
                },
            ],
            "nodes": [
                {
                    "name": "amlight_Novi01",
                    "id": "urn:sdx:node:amlight.net:B1",
                    "location": {
                        "address": "Miami",
                        "latitude": 25.75633040531146,
                        "longitude": -80.37676058477908
                    },
                    "ports": [
                        {
                            "id": "urn:sdx:port:amlight:B1:1",
                            "name": "Novi01_1",
                            "node": "urn:sdx:node:amlight.net:B1",
                            "type": "10GE",
                            "status": "up",
                            "state": "enabled",
                            "services": "l2vpn",
                            "nni": "False",
                            "mtu": 9000
                        },
                        {
                            "id": "urn:sdx:port:amlight.net:B1:2",
                            "name": "Novi01_2",
                            "node": "urn:sdx:node:amlight.net:B1",
                            "type": "25GE",
                            "status": "up",
                            "state": "enabled",
                            "services": "l2vpn",
                            "nni": "False",
                            "mtu": 9000
                        },
                        {
                            "id": "urn:sdx:port:amlight.net:B1:3",
                            "name": "Novi01_3",
                            "node": "urn:sdx:node:amlight.net:B1",
                            "type": "40GE",
                            "status": "up",
                            "state": "enabled",
                            "services": "l2vpn",
                            "nni": "False",
                            "mtu": 9000
                        }
                    ],
                },
                {
                    "name": "amlight_Novi02",
                    "id": "urn:sdx:node:amlight.net:B2",
                    "location": {
                        "address": "BocaRaton",
                        "latitude": 26.381437356374075,
                        "longitude": -80.10225977485742
                    },
                    "ports": [
                        {
                            "id": "urn:sdx:port:amlight.net:B2:1",
                            "name": "Novi02_1",
                            "node": "urn:sdx:node:amlight.net:B2",
                            "type": "50GE",
                            "status": "up",
                            "state": "enabled",
                            "services": "l2vpn",
                            "nni": "False",
                            "mtu": 9000
                        },
                        {
                            "id": "urn:sdx:port:amlight.net:B2:2",
                            "name": "Novi02_2",
                            "node": "urn:sdx:node:amlight.net:B2",
                            "type": "100GE",
                            "status": "up",
                            "state": "enabled",
                            "services": "l2vpn",
                            "nni": "False",
                            "mtu": 9000
                        },
                        {
                            "id": "urn:sdx:port:amlight.net:B2:3",
                            "name": "Novi02_3",
                            "node": "urn:sdx:node:amlight.net:B2",
                            "type": "400GE",
                            "status": "up",
                            "state": "enabled",
                            "services": "l2vpn",
                            "nni": "False",
                            "mtu": 9000
                        }
                    ],
                },
                {
                    "name": "amlight_Novi100",
                    "id": "urn:sdx:node:amlight.net:A1",
                    "location": {
                        "address": "redclara",
                        "latitude": 30.34943181039702,
                        "longitude": -81.66666016473143
                    },
                    "ports": [
                        {
                            "id": "urn:sdx:port:amlight.net:A1:1",
                            "name": "Novi100_1",
                            "node": "urn:sdx:node:amlight.net:A1",
                            "type": "10GE",
                            "status": "up",
                            "state": "enabled",
                            "services": "l2vpn",
                            "nni": "False",
                            "mtu": 9000
                        },
                        {
                            "id": "urn:sdx:port:amlight.net:A1:2",
                            "name": "Novi100_2",
                            "node": "urn:sdx:node:amlight.net:A1",
                            "type": "25GE",
                            "status": "up",
                            "state": "enabled",
                            "services": "l2vpn",
                            "nni": "False",
                            "mtu": 9000
                        }
                    ],
                }
            ],
        }
