#########
Changelog
#########
All notable changes to the kytos-sdx NApp will be documented in this file.

[UNRELEASED] - Under development
********************************

General Information
===================
-

Added
=====
-

Changed
=======
-

Fixed
=====


[3.2.0] - 2025-12-01
********************

Added
=====

- Topology export from Kytos-ng to SDX-LC using the official Topology Data Model.
- Support for provisioning L2VPN point-to-point services (MEF EVCs) using SDX-LC as orchestrator.
- “New” L2VPN API (`/api/kytos/sdx/l2vpn/1.0`) with resources to create, edit, list, and delete services.
- “Legacy” provisioning API (`/api/kytos/sdx/v1/l2vpn_ptp`) maintained for compatibility.
- Support for `entities` into SDX Port objects.
- Support for flexible VLAN configurations using interface metadata `sdx_vlan_range`.
- Support for marking interfaces as NNI links through `sdx_nni` metadata for multi-domain topologies.
- Support for standard Kytos metadata fields (switch name, port MTU, geographic details, link BW/latency/packet-loss/availability, etc.).
- Continuous integration workflows (GitHub Actions) and coverage reporting.
- Unit tests and test structure under `tests/`.

Changed
=======

- Improved documentation in `README.rst` describing metadata fields and topology export behavior.
- Updated Dockerfile and development workflow for compatibility with Kytos-ng.

Fixed
=====

- Increased size for SDX Link object
- Various internal improvements and bug fixes in topology export and L2VPN provisioning logic.
- Enhanced validation for interface metadata and VLAN range inputs.
- Avoid blocking setup() when loading topology



[0.1.0] – 2022-06-22
********************


Added
=====

- Introduction of the **kytos-sdx** NApp for integrating AtlanticWave-SDX capabilities into Kytos-ng.
- First implementation of topology export to SDX Local Controller (SDX-LC).
- Initial L2VPN provisioning workflow for point-to-point EVCs.
- Basic configuration templates, Dockerfile, and setup tools.
- Initial metadata handling for SDX VLAN ranges and NNI flagging.
- Initial test suite and CI configuration.
