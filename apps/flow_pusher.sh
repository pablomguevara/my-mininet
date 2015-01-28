#!/bin/bash

#Flow pusher script
#
#Pablo M. Guevara <pablomguevara@gmail.com>
#

# Example flow configuration for the asymmetric configuration
# NO DHCP FIRST
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# DPID 1 - Core
# Port 1 gw
# Port 2 a1
# Port 3 a2
# Port 4 a3
# Downstream
# Start by flooding
curl -X POST -d '{"dpid": "1","match": {"in_port":"1"}, "hard_timeout": "0", "idle_timeout": "0", "actions": [{"type":"OUTPUT", "port": 4294967291}]}' http://argenta2:8080/stats/flowentry/add 

# Upstream
# All goes to port 1
curl -X POST -d '{"dpid": "1","match": {"in_port":"2"}, "hard_timeout": "0", "idle_timeout": "0", "actions": [{"type": "OUTPUT", "port": "1"}]}' http://argenta2:8080/stats/flowentry/add
curl -X POST -d '{"dpid": "1","match": {"in_port":"3"}, "hard_timeout": "0", "idle_timeout": "0",  "actions": [{"type": "OUTPUT", "port": "1"}]}' http://argenta2:8080/stats/flowentry/add
curl -X POST -d '{"dpid": "1","match": {"in_port":"4"}, "hard_timeout": "0", "idle_timeout": "0",  "actions": [{"type": "OUTPUT", "port": "1"}]}' http://argenta2:8080/stats/flowentry/add

sleep 1

# DPID 2 - a1 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Port 1-3 hosts
#
# Downstream
# Start by flooding
curl -X POST -d '{"dpid": "2","match": {"in_port":"1"}, "hard_timeout": "0", "idle_timeout": "0", "actions": [{"type":"OUTPUT", "port": 4294967291}]}' http://argenta2:8080/stats/flowentry/add 

# Upstream
# All goes to port 1
curl -X POST -d '{"dpid": "2","match": {"in_port":"2"}, "hard_timeout": "0", "idle_timeout": "0", "actions": [{"type": "OUTPUT", "port": "1"}]}' http://argenta2:8080/stats/flowentry/add
curl -X POST -d '{"dpid": "2","match": {"in_port":"3"}, "hard_timeout": "0", "idle_timeout": "0", "actions": [{"type": "OUTPUT", "port": "1"}]}' http://argenta2:8080/stats/flowentry/add
curl -X POST -d '{"dpid": "2","match": {"in_port":"4"}, "hard_timeout": "0", "idle_timeout": "0", "actions": [{"type": "OUTPUT", "port": "1"}]}' http://argenta2:8080/stats/flowentry/add

sleep 1

# DPID 3 - a1 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Port 1-3 hosts
#
# Downstream
# Start by flooding
curl -X POST -d '{"dpid": "3","match": {"in_port":"1"}, "hard_timeout": "0", "idle_timeout": "0", "actions": [{"type":"OUTPUT", "port": 4294967291}]}' http://argenta2:8080/stats/flowentry/add

# Upstream
# All goes to port 1
curl -X POST -d '{"dpid": "3","match": {"in_port":"2"}, "hard_timeout": "0", "idle_timeout": "0", "actions": [{"type": "OUTPUT", "port": "1"}]}' http://argenta2:8080/stats/flowentry/add
curl -X POST -d '{"dpid": "3","match": {"in_port":"3"}, "hard_timeout": "0", "idle_timeout": "0", "actions": [{"type": "OUTPUT", "port": "1"}]}' http://argenta2:8080/stats/flowentry/add
curl -X POST -d '{"dpid": "3","match": {"in_port":"4"}, "hard_timeout": "0", "idle_timeout": "0", "actions": [{"type": "OUTPUT", "port": "1"}]}' http://argenta2:8080/stats/flowentry/add

sleep 1

# DPID 4 - a1 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Port 1-3 hosts
#
# Downstream
# Start by flooding
curl -X POST -d '{"dpid": "4","match": {"in_port":"1"}, "hard_timeout": "0", "idle_timeout": "0", "actions": [{"type":"OUTPUT", "port": 4294967291}]}' http://argenta2:8080/stats/flowentry/add 

# Upstream
# All goes to port 1
curl -X POST -d '{"dpid": "4","match": {"in_port":"2"}, "hard_timeout": "0", "idle_timeout": "0", "actions": [{"type": "OUTPUT", "port": "1"}]}' http://argenta2:8080/stats/flowentry/add
curl -X POST -d '{"dpid": "4","match": {"in_port":"3"}, "hard_timeout": "0", "idle_timeout": "0", "actions": [{"type": "OUTPUT", "port": "1"}]}' http://argenta2:8080/stats/flowentry/add
curl -X POST -d '{"dpid": "4","match": {"in_port":"4"}, "hard_timeout": "0", "idle_timeout": "0", "actions": [{"type": "OUTPUT", "port": "1"}]}' http://argenta2:8080/stats/flowentry/add

sleep 1



# ryu / ryu / app / ofctl_rest.py
# REST API
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Retrieve the switch stats
#
# get the list of all switches
# GET /stats/switches
#
# get the desc stats of the switch
# GET /stats/desc/<dpid>
#
# get flows stats of the switch
# GET /stats/flow/<dpid>
#
# get flows stats of the switch filtered by the fields
# POST /stats/flow/<dpid>
#
# get ports stats of the switch
# GET /stats/port/<dpid>
#
# get meter features stats of the switch
# GET /stats/meterfeatures/<dpid>
#
# get meter config stats of the switch
# GET /stats/meterconfig/<dpid>
#
# get meters stats of the switch
# GET /stats/meter/<dpid>
#
# get group features stats of the switch
# GET /stats/groupfeatures/<dpid>
#
# get groups desc stats of the switch
# GET /stats/groupdesc/<dpid>
#
# get groups stats of the switch
# GET /stats/group/<dpid>
#
# get ports description of the switch
# GET /stats/portdesc/<dpid>
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Update the switch stats
#
# add a flow entry
# POST /stats/flowentry/add
#
# modify all matching flow entries
# POST /stats/flowentry/modify
#
# modify flow entry strictly matching wildcards and priority
# POST /stats/flowentry/modify_strict
#
# delete all matching flow entries
# POST /stats/flowentry/delete
#
# delete flow entry strictly matching wildcards and priority
# POST /stats/flowentry/delete_strict
#
# delete all flow entries of the switch
# DELETE /stats/flowentry/clear/<dpid>
#
# add a meter entry
# POST /stats/meterentry/add
#
# modify a meter entry
# POST /stats/meterentry/modify
#
# delete a meter entry
# POST /stats/meterentry/delete
#
# add a group entry
# POST /stats/groupentry/add
#
# modify a group entry
# POST /stats/groupentry/modify
#
# delete a group entry
# POST /stats/groupentry/delete
#
# modify behavior of the physical port
# POST /stats/portdesc/modify
#
#
# send a experimeter message
# POST /stats/experimenter/<dpid>
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#curl -G http://argenta2:8080/v1.0/topology/switches
#curl -G http://argenta2:8080/v1.0/topology/switches/1
#curl -G http://argenta2:8080/v1.0/topology/switches/00:00:00:00:00:00:01
#curl -G http://argenta2:8080/v1.0/topology/switches/0000000000000001
#curl -G http://argenta2:8080/v1.0/topology/links/0000000000000001
#curl -G http://argenta2:8080/v1.0/topology/links/
#curl -G http://argenta2:8080/v1.0/topology/links
#curl -G http://argenta2:8080/v1.0/topology/switches
#wscat -c ws://argenta2:8080/v1.0/topology/ws
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# MAC PUT EX
#curl -X put -d '{"mac" : "ae:d3:3d:ad:2f:33", "port" : 1}' http://argenta2:8080/simpleswitch/mactable/0000000000000001
#curl -X PUT -d '{"mac" : "ae:d3:3d:ad:2f:33", "port" : 1}' http://argenta2:8080/simpleswitch/mactable/0000000000000001
#curl -X PUT -d '{"mac" : "ae:d3:3d:ad:2f:FF", "port" : 1}' http://argenta2:8080/simpleswitch/mactable/0000000000000001
#curl -X PUT -d '{"mac" : "22:22:22:22:22:22", "port" : 1}' http://argenta2:8080/simpleswitch/mactable/0000000000000001
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# curl -G http://argenta2:8080/stats/flow/1
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


exit 0
