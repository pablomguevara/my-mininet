#!/usr/bin/python

"""

By Pablo Guevara <pablomguevara@gmail.com>

Script to test mininet topologies with dhcp
If you have a router with DHCP server listening on eth0 you should
get an ip address. Or you could run a dhcp server listening on eth0.

Note that for some reason, connectivity after DHCP transaction is broken.
Connectivity on local subnet works, but there is no external world connecti
vity (for internet access use dhcp.py or nat+dhcp.py)

Updated Note: I see DHCPOFFER go out h1-eth0, but nothing is geting
to eth0, this script is not working.

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

def testNetwork():
  info( '*** Creating network\n' )
  
  # add remote controller
  net = Mininet( controller=lambda a: RemoteController(a, ip='127.0.0.1', port=6633 ))
  net.addController('c0')
  
  # add switch and external if
  s1 = net.addSwitch('s1')
  Intf('eth0',node = s1, port=1)
  
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
  net.stop()
  
if __name__ == '__main__':
  setLogLevel('info')
  testNetwork()
