|Stable| |Tag| |License| |Build| |Coverage|

.. raw:: html

  <div align="center">
    <h1><code>kyto-ng/sdx</code></h1>

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


General Information
===================

The SDX Napp supports topology operations and L2VPN provisioning operations. Some examples:

- Show the Kytos-ng SDX Topology:

.. code-block:: shell

	curl -s -X GET http://127.0.0.1:8181/api/kytos/sdx/topology/2.0.0

- Submit the Kytos-ng SDX Topology to SDX-LC (push topology sharing method):

.. code-block:: shell

	curl -s -X POST http://127.0.0.1:8181/api/kytos/sdx/topology/2.0.0

- Create a L2VPN using the *old* Provisioning APIs (currently being used by SDX-LC):

.. code-block:: shell

	curl -s -X POST -H 'Content-type: application/json' http://127.0.0.1:8181/api/kytos/sdx/v1/l2vpn_ptp -d '{"name": "AMPATH_vlan_503_503", "uni_a": {"port_id": "urn:sdx:port:ampath.net:Ampath3:50", "tag": {"value": 501, "tag_type": 1}}, "uni_z": {"port_id": "urn:sdx:port:ampath.net:Ampath1:40", "tag": {"value": 501, "tag_type": 1}}, "dynamic_backup_path": true}'

- Delete a L2VPN using the *old* Provisioning APIs (currently being used by SDX-LC):

.. code-block:: shell

	curl -s -X DELETE -H 'Content-type: application/json' http://127.0.0.1:8181/api/kytos/sdx/v1/l2vpn_ptp -d '{"name": "AMPATH_vlan_503_503", "uni_a": {"port_id": "urn:sdx:port:ampath.net:Ampath3:50", "tag": {"value": 501, "tag_type": 1}}, "uni_z": {"port_id": "urn:sdx:port:ampath.net:Ampath1:40", "tag": {"value": 501, "tag_type": 1}}, "dynamic_backup_path": true}'

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

- Delete a L2VPN using the *new* Provisioning API:

.. code-block:: shell

	curl -s -X DELETE http://127.0.0.1:8181/api/kytos/sdx/l2vpn/1.0/ea492fd1238e4a

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
