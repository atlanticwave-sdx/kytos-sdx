|Stable| |Tag| |License| |Build| |Coverage|

.. raw:: html

  <div align="center">
    <h1><code>kytos-ng/sdx</code></h1>

    <strong>Kytos-ng Napp that implements SDX Integration</strong>
  </div>


Overview
========

This Napp allows the integration of AtlanticWave SDX components into Kytos-ng
SDN orchestrator. The integration allows Kytos-ng sending the network Topology
to SDX-LocalController, following the Topology Data Model Specification, as well
as provisioning and operation of L2VPN Point-to-Point.

Getting started
===============

To install this NApp, first, make sure to have the same venv activated as you have ``kytos`` installed on:

.. code:: shell

   $ git clone https://github.com/atlanticwave-sdx/kytos-sdx
   $ cd kytos-sdx
   $ python3 setup.py develop

The easiest way of using this Napp is through the Docker container:

.. code:: shell

   $ docker build -t kytos-sdx .
   $ docker exec -it mongo mongo --eval 'db.getSiblingDB("kytos").createUser({user: "kytos", pwd: "kytos", roles: [ { role: "dbAdmin", db: "kytos" } ]})'
   $ docker run -d --name kytos-sdx --link mongo -e SDXLC_URL=http://192.168.0.100:8080/SDX-LC/2.0.0/topology -e OXPO_NAME=Test-OXP -e OXPO_URL=test-oxp.net -e MONGO_DBNAME=kytos -e MONGO_USERNAME=kytos -e MONGO_PASSWORD=kytos -e MONGO_HOST_SEEDS=mongo:27017 -p 8181:8181 kytos-sdx

Requirements
============

- `kytos/topology <https://github.com/kytos-ng/topology>`_
- `kytos/mef_eline <https://github.com/kytos-ng/mef_eline>`_

Kytos configuration
===================

The Kytos SDX Napp exports information about the Kytos topology to the SDX Local Controller. Thus, some information needs to be configured on the Kytos topology to enable the SDX Napps to export them. Here are some configs needed:

- `Switch.metadata.iso3166_2_lvl4`: this metadata should be set to a string containing the short and unique alphanumeric codes representing the state (or other administrative divisions) and country. Example: "FL-US" (Florida - USA). Another example: "SP-BR" (Sao Paulo - Brazil)

- `Interface.metadata.sdx_vlan_range`: VLAN range that should be allowed for SDX to use when creating point-to-point L2VPN on Kytos (aka MEF-Eline EVCs). The format for this attribute is a list of tuples, where each tuple contains the range's first and last VLAN ID. Example: [[1, 4095]] (include all VLANs). Another example: [[1, 100], [300, 300]] (include VLANs 1 to 100 and VLAN 300)

- `Interface.metadata.sdx_nni`: the `sdx_nni` attribute must only be set if that interface connects your OXP to another OXP (the boundary between two domains). In this case, it has to be a string representing the remote OXP's Port ID (format: "urn:sdx:port:<oxp_url>:<node_name>:<port_name>"). Example: suppose the port is an AmLight port connected to ZAOXI OXP, with the remote node at ZAOXI being "s1" and remote port at ZAOXI being "50" then the `sdx_nni` attribute on the AmLight topology side is set to "urn:sdx:port:zaoxi.ac.za:s1:50".

- `Interface.metadata.entities`: This attribute is an unrestricted list of strings, where each string could be the name, acronym, autonomous system number, or any other descriptive approach.

Besides the specific metadata above, other well-known Kytos metadata are also used:

- `Switch.metadata.node_name`: string which represents the Switch Name (SDX Napp will allow only ASCII and a few special characters: "." (period), "," (comma), "-" (dash), "_" (underscore)", and "/" (forward slash). Moreover, SDX Napp will truncate the name to 30 characters)

- `Switch.metadata.lat`: latitude

- `Switch.metadata.lng`: longitude

- `Switch.metadata.address`: address

- `Interface.metadata.port_name`: string which represents the port name/description (SDX Napp will allow only ASCII and a few special characters: "." (period), "," (comma), "-" (dash), "_" (underscore)", and "/" (forward slash). Moreover, SDX Napp will truncate the name to 30 characters)

- `Interface.metadata.mtu`: MTU of the port. If not set, it defaults to 1500.

- `Interface.metadata.entities`: The entities attribute describes the facilities/institutions connected to the port (universities, research facilities, research and education networks, and instruments). This is an unrestricted list of strings, where each string could be the name, acronym, autonomous system number, or any other descriptive approach. (example: `"entities": ["FIU", "Florida International University"]`)

- `Link.metadata.link_name`: string which represents the link name/description (SDX Napp will allow only ASCII and a few special characters: "." (period), "," (comma), "-" (dash), "_" (underscore)", and "/" (forward slash). Moreover, SDX Napp will truncate the name to 30 characters)

- `Link.metadata.residual_bandwidth`: attribute describes the average bandwidth available for the link. If not set, defaults to 100.

- `Link.metadata.latency`: attribute describes the delay introduced by the Link object in milliseconds to the end-to-end path. If not set, defaults to 0.

- `Link.metadata.packet_loss`: This attribute describes the percentage of packet loss observed for the link. If not set, it defaults to 0.

- `Link.metadata.availability`: attribute describes the percentage of time the link has been available for data transmission. If not set, defaults to 100.

Finally, it is possible to filter out which components of the topology you want to export to SDX: Switches, Interfaces and Links. To filter out the components of the topology, you can define the settings attribute `SDX_DEF_INCLUDE` (defaults to True for all components, meaning all items are enabled) and then define a metadata attribute on each component named `sdx_include` (boolean). For example, if you want to export the whole topology except one particular interface, you must keep `SDX_DEF_INCLUDE={"switch": True, "link": True, "interface": True}` and then set the specific interface metadata with `sdx_include=False`. The same happens all the way around: if you only want to include certain switches and specific interfaces, then you should set the `SDX_DEF_INCLUDE={"switch": False, "interface": True, "link": True}` and set the `sdx_include=True` on the items you want to export. Be aware that if you set a switch with `sdx_include=False`, all interfaces on that switch and links to that switch will NOT be included.

General Information
===================

The SDX Napp supports topology operations and L2VPN provisioning operations. Some examples:


Get Kytos-ng SDX Topology
******************************

.. code-block:: shell

	curl -s -X GET http://127.0.0.1:8181/api/kytos/sdx/topology/2.0.0

Send Topology to SDX-LC
************************

- Submit the Kytos-ng SDX Topology to SDX-LC (push topology sharing method):

.. code-block:: shell

	curl -s -X POST http://127.0.0.1:8181/api/kytos/sdx/topology/2.0.0

Create L2VPN with old API
*************************

- Create a L2VPN using the *old* Provisioning APIs (currently being used by SDX-LC):

.. code-block:: shell

	curl -s -X POST -H 'Content-type: application/json' http://127.0.0.1:8181/api/kytos/sdx/v1/l2vpn_ptp -d '{"name": "AMPATH_vlan_503_503", "uni_a": {"port_id": "urn:sdx:port:ampath.net:Ampath3:50", "tag": {"value": 501, "tag_type": 1}}, "uni_z": {"port_id": "urn:sdx:port:ampath.net:Ampath1:40", "tag": {"value": 501, "tag_type": 1}}, "dynamic_backup_path": true}'

Delete L2VPN with old API
*************************

- Delete a L2VPN using the *old* Provisioning APIs (currently being used by SDX-LC):

.. code-block:: shell

	curl -s -X DELETE -H 'Content-type: application/json' http://127.0.0.1:8181/api/kytos/sdx/v1/l2vpn_ptp -d '{"name": "AMPATH_vlan_503_503", "uni_a": {"port_id": "urn:sdx:port:ampath.net:Ampath3:50", "tag": {"value": 501, "tag_type": 1}}, "uni_z": {"port_id": "urn:sdx:port:ampath.net:Ampath1:40", "tag": {"value": 501, "tag_type": 1}}, "dynamic_backup_path": true}'

Create L2VPN with new API
*************************

- Create a L2VPN using the *new* Provisioning API (many examples):

.. code-block:: shell

	# Example 01: minimal attributes (requierd)
	curl -s -X POST -H 'Content-type: application/json' http://127.0.0.1:8181/api/kytos/sdx/l2vpn/1.0 -d '{"name": "AMPATH_vlan_501_501", "endpoints": [{"port_id": "urn:sdx:port:ampath.net:Ampath3:50", "vlan": "501"}, {"port_id": "urn:sdx:port:ampath.net:Ampath1:40", "vlan": "501"}]}'

	# Example 02: minimal attributes with endpoint.0 being all (frames with and without 802.1q headers)
	curl -s -X POST -H 'Content-type: application/json' http://127.0.0.1:8181/api/kytos/sdx/l2vpn/1.0 -d '{"name": "AMPATH_vlan_all_503", "endpoints": [{"port_id": "urn:sdx:port:ampath.net:Ampath3:50", "vlan": "all"}, {"port_id": "urn:sdx:port:ampath.net:Ampath1:40", "vlan": "503"}]}'

	# Example 03: range of VLAN
	curl -s -X POST -H 'Content-type: application/json' http://127.0.0.1:8181/api/kytos/sdx/l2vpn/1.0 -d '{"name": "AMPATH_vlan_512:534_512:534", "endpoints": [{"port_id": "urn:sdx:port:ampath.net:Ampath3:50", "vlan": "512:534"}, {"port_id": "urn:sdx:port:ampath.net:Ampath1:40", "vlan": "512:534"}]}'

	# Example 04: example with all possible attributes
	curl -s -X POST -H 'Content-type: application/json' http://127.0.0.1:8181/api/kytos/sdx/l2vpn/1.0 -d '{"name": "AMPATH_vlan_503_503", "endpoints": [{"port_id": "urn:sdx:port:ampath.net:Ampath3:50", "vlan": "501"}, {"port_id": "urn:sdx:port:ampath.net:Ampath1:40", "vlan": "501"}], "description": "test foobar xpto aa bbb", "scheduling": {"start_time": "2024-08-07T19:55:00Z", "end_time": "2024-08-07T19:58:00Z"}, "notifications": [{"email": "user@domain.com"},{"email": "user2@domain2.com"}], "qos_metrics": {"min_bw": {"value": 5,"strict": false}, "max_delay": {"value": 150, "strict": true}}}'

	# Example 05: minimal attributes with endpoint.0 being untagged (frames without 802.1q header)
	curl -s -X POST -H 'Content-type: application/json' http://127.0.0.1:8181/api/kytos/sdx/l2vpn/1.0 -d '{"name": "AMPATH_vlan_untagged_503", "endpoints": [{"port_id": "urn:sdx:port:ampath.net:Ampath3:50", "vlan": "untagged"}, {"port_id": "urn:sdx:port:ampath.net:Ampath1:40", "vlan": "503"}]}'


Edit L2VPN with new API
*************************

- Editing a L2VPN using the *new* Provisioning API:

.. code-block:: shell

        curl -H 'Content-type: application/json' -X PATCH http://127.0.0.1:8181/api/kytos/sdx/l2vpn/1.0/f9ecff1309d845 -d '{"endpoints": [{"port_id": "urn:sdx:port:ampath.net:Ampath3:50", "vlan": "301"}, {"port_id": "urn:sdx:port:ampath.net:Ampath1:40", "vlan": "4095"}], "description": "this is a l2vpn test"}'

The example above changes the endpoints and the description of a L2VPN. Fields that can be changed: endpoints, description, scheduling, qos_metrics, name. Note about endpoints: if one endpoint has to be changed, you must provide both endpoints.


Delete L2VPN with new API
*************************

- Delete a L2VPN using the *new* Provisioning API:

.. code-block:: shell

	curl -s -X DELETE http://127.0.0.1:8181/api/kytos/sdx/l2vpn/1.0/ea492fd1238e4a

Get L2VPN with new API
*************************

- Get a L2VPN using the *new* Provisioning API:

.. code-block:: shell

	curl -s http://127.0.0.1:8181/api/kytos/sdx/l2vpn/1.0/ea492fd1238e4a

.. TAGs

.. |Stable| image:: https://img.shields.io/badge/stability-stable-green.svg
   :target: https://github.com/atlanticwave-sdx/kytos-sdx
.. |Build| image:: https://github.com/atlanticwave-sdx/kytos-sdx/actions/workflows/test.yml/badge.svg
  :alt: Build status
.. |Coverage| image:: https://coveralls.io/repos/github/atlanticwave-sdx/kytos-sdx/badge.svg
  :alt: Code coverage
.. |Tag| image:: https://img.shields.io/github/tag/atlanticwave-sdx/kytos-sdx.svg
   :target: https://github.com/atlanticwave-sdx/kytos-sdx/tags
.. |License| image:: https://img.shields.io/github/license/atlanticwave-sdx/kytos-sdx.svg
   :target: https://github.com/atlanticwave-sdx/kytos-sdx/blob/master/LICENSE
