#!/usr/bin/python

"""
By Pablo Guevara <pablomguevara@gmail.com>

Script to test mininet topologies with dhcp
Creates a host on rootname space to link switch to outside world
If you have a router with DHCP server listening on eth0 you should
get an ip address.

"""

import re, sys
from mininet.cli import CLI
from mininet.log import setLogLevel, info, error
from mininet.net import Mininet
from mininet.link import Intf
from mininet.topolib import TreeTopo
from mininet.util import quietRun
from mininet.node import RemoteController
from mininet.node import Node

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
  
  # add remote controller
  net = Mininet( controller=lambda a: RemoteController(a, ip='127.0.0.1', port=6633 ))
  net.addController('c0')
  
  # add host
  s1 = net.addSwitch('s1')
  
  # the following cmd adds eth0.145 and eth0.146 interface to s1
  #_intf = Intf('eth0', node = s1)
  
  #TODO
  # The host on root name space approach works well for nat/routed application
  # when trying to bridge traffic, I can not get the hosts to get to the
  # internet
  root = net.addHost('root', ip='0.0.0.0', inNamespace=False)
  
  # Prevent network-manager from interfering with our interface 
  fixNetworkManager( root, 'root-eth0' )
  
  # Add link to switch
  link = net.addLink(root,s1)
  
  # Configure iptables
  root.cmd( 'iptables -F' )
  root.cmd( 'iptables -t nat -F' )
  root.cmd( 'iptables -P FORWARD ACCEPT' )
  root.cmd( 'iptables -P INTPUT ACCEPT' )
  root.cmd( 'iptables -P OUTPUT ACCEPT' )
  # Configure Linux bridge
  root.cmd( 'ifconfig virbr0 down' )
  root.cmd( 'brctl delbr virbr0' )
  root.cmd( 'brctl addbr br0' )
  root.cmd( 'brctl addif br0 eth0 root-eth0' )
  root.cmd( 'ifconfig br0 up' )
  
  # add hosts
  h1 = net.addHost('h1', ip='0.0.0.0', mac='00:00:00:00:00:01')
  h2 = net.addHost('h2', ip='0.0.0.0', mac='00:00:00:00:00:02')

  # add links
  net.addLink(h1,s1)
  net.addLink(h2,s1)
  
  # start network
  net.start()
  
  # start dhcp
  h1.cmd('dhclient h1-eth0 &')
  h2.cmd('dhclient h2-eth0 &')
  
  net.startTerms()
    
  CLI( net )
  
  #Clean up
  root.cmd( 'ifconfig br0 down' )
  root.cmd( 'brctl delbr br0' )
  
  net.stop()
  
if __name__ == '__main__':
  setLogLevel('info')
  testNetwork()
