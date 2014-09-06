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
  #Intf('eth0.145', node = s1)
  #Intf('eth0.146', node = s1)
  
  # add hosts
  h1 = net.addHost('h1')
  h2 = net.addHost('h2')
  
  # add links
  net.addLink(h1,s1)
  net.addLink(h2,s1)
  
  # start network
  net.start()
  
  # add vlan interfaces on hosts
  h1.cmd('vconfig add h1-eth0 145')
  h2.cmd('vconfig add h2-eth0 145')
  h1.cmd('vconfig add h1-eth0 146')
  h2.cmd('vconfig add h2-eth0 146')
  
  # bring up interfaces
  #h1.cmd('ifconfig h1-eth0.145 up')
  #h2.cmd('ifconfig h2-eth0.145 up')
  h1.cmd('ifconfig h1-eth0.146 up')
  h2.cmd('ifconfig h2-eth0.146 up')
  h1.cmd('ifconfig h1-eth0.145 192.168.145.3 netmask 255.255.255.0 up')
  h2.cmd('ifconfig h2-eth0.145 192.168.145.4 netmask 255.255.255.0 up')

  # start dhcp
  #h1.cmd('dhclient h1-eth0.145 &')
  #h2.cmd('dhclient h2-eth0.145 &')
  h1.cmd('dhclient h1-eth0.146 &')
  h2.cmd('dhclient h2-eth0.146 &')
  
  CLI( net )
  net.stop()
  
if __name__ == '__main__':
  setLogLevel('info')
  testNetwork()
