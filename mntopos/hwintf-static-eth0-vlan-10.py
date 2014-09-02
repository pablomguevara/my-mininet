#!/usr/bin/python
import re, sys

"""

By Pablo Guevara <pablomguevara@gmail.com>

Script to test mininet topologies with static IP and vlan
Remote local controler
Subnet 192.168.10.0/24
Root Node acting as router 192.168.10.10


"""

import os

from mininet.cli import CLI
from mininet.log import setLogLevel, info, error
from mininet.net import Mininet
from mininet.link import Intf
from mininet.topolib import TreeTopo
from mininet.util import quietRun
from mininet.node import Node
from mininet.node import RemoteController


def addNode( network, nodename, switch='s1', ipaddr='10.254', subnet='10.0/8',
    inNs=False, inetIntf='eth0' ):
    """Add Generic Node
       switch: switch to connect dhcp
       ipaddr: address for interface in dhcp
       subnet: Mininet subnet
       inNs: False, the node to be added is on root namespace"""
    
    switch = network.get( switch )
    prefixLen = subnet.split( '/' )[ 1 ]

    # Create a node
    N = Node( name=nodename, inNamespace=inNs )   
    
    # Prevent network-manager from interfering with our interface 
    fixNetworkManager( N, nodename + '-' + inetIntf )

    # Create link between dhcp NS and switch
    link = network.addLink( N, switch )
    link.intf1.setIP( ipaddr, prefixLen )
    
    return N


def fixNetworkManager( root, intf ):
    """Prevent network-manager from messing with our interface,
       by specifying manual configuration in /etc/network/interfaces
       root: a node in the root namespace (for running commands)
       intf: interface name"""
    cfile = '/etc/network/interfaces'
    line = '\niface %s inet manual\n' % intf
    config = open( cfile ).read()
    if line not in config:
        print '*** Adding', line.strip(), 'to', cfile
        with open( cfile, 'a' ) as f:
            f.write( line )
        # Probably need to restart network-manager to be safe -
        # hopefully this won't disconnect you
        root.cmd( 'service network-manager restart' )


def testNetwork():
  info( '*** Creating network\n' )
  net = Mininet( controller=lambda a: RemoteController(a, ip='127.0.0.1', port=6633))
  net.addController('c0')
  
  # add switch
  s1 = net.addSwitch('s1')

  # Add hosts
  h1 = net.addHost('h1', ip='10.0.0.1', mac='00:00:00:00:00:01') 
  h2 = net.addHost('h2', ip='10.0.0.2', mac='00:00:00:00:00:02')
  
  # add links
  net.addLink(h1,s1)
  net.addLink(h2,s1)
  
  # start network
  net.start()

  # Add Router
  root = addNode( net, 'root', ipaddr='10.0.0.253', subnet='10.0.0.0/8',
      inetIntf='eth0')
  
  # add vlans
  root.cmd('vconfig add root-eth0 10')
  h1.cmd('vconfig add h1-eth0 10')
  h2.cmd('vconfig add h2-eth0 10')
  
  # add ip addresses on vlan 10
  root.cmd('ifconfig root-eth0.10 192.168.10.253 netmask 255.255.255.0 up')
  h1.cmd('ifconfig h1-eth0.10 192.168.10.101 netmask 255.255.255.0 up')
  h2.cmd('ifconfig h2-eth0.10 192.168.10.102 netmask 255.255.255.0 up')
  
  CLI( net )
  net.stop()

if __name__ == '__main__':
  setLogLevel('info')
  testNetwork()

