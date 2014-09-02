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

def testNetwork():
  info( '*** Creating network\n' )
  net = Mininet( controller=lambda a: RemoteController(a, ip='127.0.0.1', port=6633))
  net.addController('c0')
  
  # add switch
  s1 = net.addSwitch('s1')
  
  # Add interface 
  _intf = Intf( 'eth0.10', node=s1 )

  # Add hosts
  h1 = net.addHost('h1', ip='0.0.0.0', mac='00:00:00:00:00:01') 
  h2 = net.addHost('h2', ip='0.0.0.0', mac='00:00:00:00:00:02')
  
  # add links
  net.addLink(h1,s1)
  net.addLink(h2,s1)
  
  # start network
  net.start()

  # add vlans
  h1.cmd('vconfig add h1-eth0 10')
  h2.cmd('vconfig add h2-eth0 10')
  
  # add ip addresses on vlan 10
  h1.cmd('ifconfig h1-eth0.10 192.168.10.101 netmask 255.255.255.0 up')
  h2.cmd('ifconfig h2-eth0.10 192.168.10.102 netmask 255.255.255.0 up')
  
  CLI( net )
  net.stop()

if __name__ == '__main__':
  setLogLevel('info')
  testNetwork()

