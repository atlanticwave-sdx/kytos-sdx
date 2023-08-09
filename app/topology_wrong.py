""" topology mock """


def topology_mock():
    """ return json data """
    return {
            "id": "urn:ogf:network:sdx:topology:amlight.net",
            "name": "AmLight-OXP",
            "model_version": "1.0.0",
            "time_stamp": "2000-01-23T04:56:07+00:00",
            "version": 1,
            "links": [
                {
                    "availability": 56.37376656633328,
                    "residual_bandwidth": 602746.015561422,
                    "id": "urn:ogf:network:sdx:link:amlight:B1-B2",
                    "latency": 146582.15146899645,
                    "name": "amlight:B1-B2",
                    "packet_loss": 59.621339166831824,
                    "ports": [
                        {
                            "id": "urn:sdx:port:amlight.net:B1:2",
                            "name": "Novi01:2",
                            "node": "urn:sdx:node:amlight.net:B1",
                            "short_name": "B1:2",
                            "label_range": ["100-200", "10001"],
                            "status": "up"
                        },
                        {
                            "id": "urn:sdx:port:amlight.net:B2:2",
                            "label_range": ["100-200", "10001"],
                            "name": "Novi02:2",
                            "node": "urn:sdx:node:amlight.net:B2",
                            "short_name": "B2:2",
                            "status": "up"
                        }
                    ],
                    "short_name": "Miami-BocaRaton",
                    "bandwidth": 80083.7389632821
                },
                {
                    "availability": 56.37376656633328,
                    "residual_bandwidth": 602746.015561422,
                    "id": "urn:ogf:network:sdx:link:amlight:A1-B1",
                    "latency": 146582.15146899645,
                    "name": "amlight:A1-B1",
                    "packet_loss": 59.621339166831824,
                    "ports": [
                        {
                            "id": "urn:sdx:port:amlight.net:A1:1",
                            "label_range": ["100-200", "1000"],
                            "name": "Novi100:1",
                            "node": "urn:sdx:node:amlight.net:A1",
                            "short_name": "A1:1",
                            "status": "up"
                        },
                        {
                            "id": "urn:sdx:port:amlight.net:B1:3",
                            "name": "Novi01:3",
                            "node": "urn:sdx:node:amlight.net:B1",
                            "short_name": "B1:3",
                            "label_range": ["100-200", "10001"],
                            "status": "up"
                        }
                    ],
                    "short_name": "redclara-miami",
                    "bandwidth": 80083.7389632821
                },
                {
                    "availability": 56.37376656633328,
                    "residual_bandwidth": 602746.015561422,
                    "id": "urn:ogf:network:sdx:link:amlight:A1-B2",
                    "latency": 146582.15146899645,
                    "name": "amlight:A1-B2",
                    "packet_loss": 59.621339166831824,
                    "ports": [
                        {
                            "id": "urn:sdx:port:amlight.net:A1:2",
                            "label_range": ["100-200", "1000"],
                            "name": "Novi100:2",
                            "node": "urn:sdx:node:amlight.net:A1",
                            "short_name": "A1:2",
                            "status": "up"
                        },
                        {
                            "id": "urn:sdx:port:amlight.net:B2:3",
                            "label_range": ["100-200", "10001"],
                            "name": "Novi02:3",
                            "node": "urn:sdx:node:amlight.net:B2",
                            "short_name": "B2:3",
                            "status": "up"
                        }
                    ],
                    "short_name": "redclara-BocaRaton",
                    "bandwidth": 80083.7389632821
                },
                {
                    "availability": 56.37376656633328,
                    "residual_bandwidth": 602746.015561422,
                    "id": "urn:ogf:network:sdx:link:nni:Miami-Sanpaolo",
                    "latency": 146582.15146899645,
                    "name": "nni:Miami-Sanpaolo",
                    "packet_loss": 59.621339166831824,
                    "nni": "True",
                    "ports": [
                        {
                            "id": "urn:sdx:port:amlight:B1:1",
                            "name": "Novi01:1",
                            "node": "urn:sdx:node:amlight.net:B1",
                            "short_name": "B1:1",
                            "label_range": ["100-200", "10001"],
                            "status": "up"
                        },
                        {
                            "id": "urn:ogf:network:sdx:port:sax:B1:1",
                            "name": "Novi01:1",
                            "node": "urn:ogf:network:sdx:port:sax:B1",
                            "short_name": "B1:1",
                            "label_range": ["100-200", "10001"],
                            "status": "up"
                        }
                    ],
                    "short_name": "Miami-Sanpaolo",
                    "bandwidth": 80083.7389632821
                },
                {
                    "availability": 56.37376656633328,
                    "residual_bandwidth": 602746.015561422,
                    "id": "urn:ogf:network:sdx:link:nni:BocaRaton-Fortaleza",
                    "latency": 146582.15146899645,
                    "name": "nni:BocaRaton-Fortaleza",
                    "packet_loss": 59.621339166831824,
                    "nni": "True",
                    "ports": [
                        {
                            "id": "urn:sdx:port:amlight.net:B2:1",
                            "label_range": ["100-200", "1000"],
                            "name": "Novi02:1",
                            "node": "urn:sdx:node:amlight.net:B2",
                            "short_name": "B2:1",
                            "status": "up"
                        },
                        {
                            "id": "urn:ogf:network:sdx:port:sax:B2:1",
                            "label_range": ["100-200", "1000"],
                            "name": "Novi02:1",
                            "node": "urn:ogf:network:sdx:node:sax:B2",
                            "short_name": "B2:1",
                            "status": "up"
                        }
                    ],
                    "short_name": "BocaRaton-Fortaleza",
                    "bandwidth": 80083.7389632821
                }
            ],
            "nodes": [
                {
                    "id": "urn:sdx:node:amlight.net:B1",
                    "location": {
                        "address": "Miami",
                        "latitude": 25.75633040531146,
                        "longitude": -80.37676058477908
                    },
                    "name": "amlight:Novi01",
                    "ports": [
                        {
                            "id": "urn:sdx:port:amlight:B1:1",
                            "name": "Novi01:1",
                            "node": "urn:sdx:node:amlight.net:B1",
                            "short_name": "B1:1",
                            "label_range": ["100-200", "10001"],
                            "status": "up"
                        },
                        {
                            "id": "urn:sdx:port:amlight.net:B1:2",
                            "name": "Novi01:2",
                            "node": "urn:sdx:node:amlight.net:B1",
                            "short_name": "B1:2",
                            "label_range": ["100-200", "10001"],
                            "status": "up"
                        },
                        {
                            "id": "urn:sdx:port:amlight.net:B1:3",
                            "name": "Novi01:3",
                            "node": "urn:sdx:node:amlight.net:B1",
                            "short_name": "B1:3",
                            "label_range": ["100-200", "10001"],
                            "status": "up"
                        }
                    ],
                    "short_name": "B1"
                },
                {
                    "id": "urn:sdx:node:amlight.net:B2",
                    "location": {
                        "address": "BocaRaton",
                        "latitude": 26.381437356374075,
                        "longitude": -80.10225977485742
                    },
                    "name": "amlight:Novi02",
                    "ports": [
                        {
                            "id": "urn:sdx:port:amlight.net:B2:1",
                            "label_range": ["100-200", "1000"],
                            "name": "Novi02:1",
                            "node": "urn:sdx:node:amlight.net:B2",
                            "short_name": "B2:1",
                            "status": "up"
                        },
                        {
                            "id": "urn:sdx:port:amlight.net:B2:2",
                            "label_range": ["100-200", "10001"],
                            "name": "Novi02:2",
                            "node": "urn:sdx:node:amlight.net:B2",
                            "short_name": "B2:2",
                            "status": "up"
                        },
                        {
                            "id": "urn:sdx:port:amlight.net:B2:3",
                            "label_range": ["100-200", "10001"],
                            "name": "Novi02:3",
                            "node": "urn:sdx:node:amlight.net:B2",
                            "short_name": "B2:3",
                            "status": "up"
                        }
                    ],
                    "short_name": "B2"
                },
                {
                    "id": "urn:sdx:node:amlight.net:A1",
                    "location": {
                        "address": "redclara",
                        "latitude": 30.34943181039702,
                        "longitude": -81.66666016473143
                    },
                    "name": "amlight:Novi100",
                    "ports": [
                        {
                            "id": "urn:sdx:port:amlight.net:A1:1",
                            "label_range": ["100-200", "1000"],
                            "name": "Novi100:1",
                            "node": "urn:sdx:node:amlight.net:A1",
                            "short_name": "A1:1",
                            "status": "up"
                        },
                        {
                            "id": "urn:sdx:port:amlight.net:A1:2",
                            "label_range": ["100-200", "1000"],
                            "name": "Novi100:2",
                            "node": "urn:sdx:node:amlight.net:A1",
                            "short_name": "A1:2",
                            "status": "up"
                        }
                    ],
                    "short_name": "A1"
                }
            ],
            "domain_service": {
                "owner": "FIU"
            }
        }
