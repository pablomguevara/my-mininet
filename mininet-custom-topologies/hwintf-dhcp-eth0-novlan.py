#!/usr/bin/python
import re, sys

from mininet.cli import CLI
from mininet.log import setLogLevel, info, error
from mininet.net import Mininet
from mininet.link import Intf
from mininet.topolib import TreeTopo
from mininet.util import quietRun
from mininet.node import RemoteController

def testNetwork():
  info( '*** Creating network\n' )
  
  # add remote controller
  net = Mininet( controller=lambda a: RemoteController(a, ip='127.0.0.1', port=6633 ))
  net.addController('c0')
  
  # add host
  s1 = net.addSwitch('s1')
  
  # the following cmd adds eth0.145 and eth0.146 interface to s1
  Intf('eth0', node = s1)
  
  # add hosts
  h1 = net.addHost('h1', ip='0.0.0.0')
  h2 = net.addHost('h2', ip='0.0.0.0')
  
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
