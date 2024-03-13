#!/bin/bash

AMLIGHT=http://0.0.0.0:8181
SAX=http://0.0.0.0:8282
TENET=http://0.0.0.0:8383

# Enable all switches
for sw in $(curl -s $AMLIGHT/api/kytos/topology/v3/switches | jq -r '.switches[].id'); do curl -H 'Content-type: application/json' -X POST $AMLIGHT/api/kytos/topology/v3/switches/$sw/enable; curl -H 'Content-type: application/json' -X POST $AMLIGHT/api/kytos/topology/v3/interfaces/switch/$sw/enable; done
for sw in $(curl -s $SAX/api/kytos/topology/v3/switches | jq -r '.switches[].id'); do curl -H 'Content-type: application/json' -X POST $SAX/api/kytos/topology/v3/switches/$sw/enable; curl -H 'Content-type: application/json' -X POST $SAX/api/kytos/topology/v3/interfaces/switch/$sw/enable; done
for sw in $(curl -s $TENET/api/kytos/topology/v3/switches | jq -r '.switches[].id'); do curl -H 'Content-type: application/json' -X POST $TENET/api/kytos/topology/v3/switches/$sw/enable; curl -H 'Content-type: application/json' -X POST $TENET/api/kytos/topology/v3/interfaces/switch/$sw/enable; done

# give a few seconds for link discovery (LLDP)
sleep 10

# enable all links
for l in $(curl -s $AMLIGHT/api/kytos/topology/v3/links | jq -r '.links[].id'); do curl -H 'Content-type: application/json' -X POST $AMLIGHT/api/kytos/topology/v3/links/$l/enable; done
for l in $(curl -s $SAX/api/kytos/topology/v3/links | jq -r '.links[].id'); do curl -H 'Content-type: application/json' -X POST $SAX/api/kytos/topology/v3/links/$l/enable; done
for l in $(curl -s $TENET/api/kytos/topology/v3/links | jq -r '.links[].id'); do curl -H 'Content-type: application/json' -X POST $TENET/api/kytos/topology/v3/links/$l/enable; done

# Amlight network operator role
curl -H 'Content-type: application/json' -X POST $AMLIGHT/api/kytos/topology/v3/switches/aa:00:00:00:00:00:00:01/metadata -d '{"lat": "25.77", "lng": "-80.19", "address": "Miami", "iso3166_2_lvl4": "US-FL"}'
curl -H 'Content-type: application/json' -X POST $AMLIGHT/api/kytos/topology/v3/switches/aa:00:00:00:00:00:00:02/metadata -d '{"lat": "26.38", "lng": "-80.11", "address": "BocaRaton", "iso3166_2_lvl4": "US-FL"}'
curl -H 'Content-type: application/json' -X POST $AMLIGHT/api/kytos/topology/v3/switches/aa:00:00:00:00:00:00:03/metadata -d '{"lat": "30.27", "lng": "-81.68", "address": "Jacksonville", "iso3166_2_lvl4": "US-FL"}'
curl -H 'Content-type: application/json' -X POST $AMLIGHT/api/kytos/topology/v3/interfaces/aa:00:00:00:00:00:00:01:40/metadata -d '{"sdx_nni": "sax.net:Sax01:40"}'
curl -H 'Content-type: application/json' -X POST $AMLIGHT/api/kytos/topology/v3/interfaces/aa:00:00:00:00:00:00:02:40/metadata -d '{"sdx_nni": "sax.net:Sax02:40"}'

# SAX network operator role
curl -H 'Content-type: application/json' -X POST $SAX/api/kytos/topology/v3/switches/dd:00:00:00:00:00:00:04/metadata -d '{"lat": "-3", "lng": "-40", "address": "Fortaleza", "iso3166_2_lvl4": "BR-CE"}'
curl -H 'Content-type: application/json' -X POST $SAX/api/kytos/topology/v3/switches/dd:00:00:00:00:00:00:05/metadata -d '{"lat": "-3", "lng": "-20", "address": "Fortaleza", "iso3166_2_lvl4": "BR-CE"}'
curl -H 'Content-type: application/json' -X POST $SAX/api/kytos/topology/v3/interfaces/dd:00:00:00:00:00:00:04:40/metadata -d '{"sdx_nni": "ampath.net:Ampath1:40"}'
curl -H 'Content-type: application/json' -X POST $SAX/api/kytos/topology/v3/interfaces/dd:00:00:00:00:00:00:04:41/metadata -d '{"sdx_nni": "tenet.ac.za:Tenet01:41"}'
curl -H 'Content-type: application/json' -X POST $SAX/api/kytos/topology/v3/interfaces/dd:00:00:00:00:00:00:05:40/metadata -d '{"sdx_nni": "ampath.net:Ampath2:40"}'
curl -H 'Content-type: application/json' -X POST $SAX/api/kytos/topology/v3/interfaces/dd:00:00:00:00:00:00:05:41/metadata -d '{"sdx_nni": "tenet.ac.za:Tenet02:41"}'

# TENET operator
curl -H 'Content-type: application/json' -X POST $TENET/api/kytos/topology/v3/switches/cc:00:00:00:00:00:00:06/metadata -d '{"lat": "-33", "lng": "18", "address": "CapeTown", "iso3166_2_lvl4": "ZA-WC"}'
curl -H 'Content-type: application/json' -X POST $TENET/api/kytos/topology/v3/switches/cc:00:00:00:00:00:00:07/metadata -d '{"lat": "-26", "lng": "28", "address": "Johanesburgo", "iso3166_2_lvl4": "ZA-GP"}'
curl -H 'Content-type: application/json' -X POST $TENET/api/kytos/topology/v3/switches/cc:00:00:00:00:00:00:08/metadata -d '{"lat": "-33", "lng": "27", "address": "EastLondon", "iso3166_2_lvl4": "ZA-EC"}'
curl -H 'Content-type: application/json' -X POST $TENET/api/kytos/topology/v3/interfaces/cc:00:00:00:00:00:00:06:41/metadata -d '{"sdx_nni": "sax.net:Sax01:41"}'
curl -H 'Content-type: application/json' -X POST $TENET/api/kytos/topology/v3/interfaces/cc:00:00:00:00:00:00:07:41/metadata -d '{"sdx_nni": "sax.net:Sax02:41"}'
