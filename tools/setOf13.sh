#!/bin/bash
# Script to set SimpleISPTopo.py switched to use OF 1.3


echo "Setting OF version 1.3"

sudo ovs-vsctl set Bridge a1 protocols=OpenFlow13
sudo ovs-vsctl set Bridge a2 protocols=OpenFlow13
sudo ovs-vsctl set Bridge a3 protocols=OpenFlow13
sudo ovs-vsctl set Bridge c1 protocols=OpenFlow13

echo "Checking version for all switches"

sudo ovs-vsctl get bridge a1 protocols
sudo ovs-vsctl get bridge a2 protocols
sudo ovs-vsctl get bridge a3 protocols
sudo ovs-vsctl get bridge c1 protocols

echo "Checking STP status for all switches"

sudo ovs-vsctl get bridge a1 stp_enable
sudo ovs-vsctl get bridge a2 stp_enable
sudo ovs-vsctl get bridge a3 stp_enable
sudo ovs-vsctl get bridge c1 stp_enable

exit 0

