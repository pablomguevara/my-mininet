#!/usr/bin/python
import re, sys

from mininet.cli import CLI
from mininet.log import setLogLevel, info, error
from mininet.net import Mininet
from mininet.link import Intf
from mininet.topolib import TreeTopo
from mininet.util import quietRun

def testNetwork():
  info( '*** Creating network\n' )
  net = Mininet( topo=None,build = False)
  net.addController(name = 'c0')
  
  s1 = net.addSwitch('s1')
  Intf('eth0.145',node = s1)
  
  #static ip
  #h1 = net.addHost('h1',ip = '192.168.145.101/24')
  #h2 = net.addHost('h2',ip = '192.168.145.102/24')
  
  #for dhcp
  h1 = net.addHost('h1',ip ='0.0.0.0') 
  h2 = net.addHost('h2',ip = '0.0.0.0')
  
  # add links
  net.addLink(h1,s1)
  net.addLink(h2,s1)
  
  # start network
  net.start()
  
  # add vconfig
  h1.cmd('vconfig h1-eth0 145')
  h2.cmd('vconfig h1-eth0 145')
  
  h1.cmd('dhclient h1-eth0.145')
  h2.cmd('dhclient h2-eth0.145')
  
  CLI( net )
  net.stop()
  
if __name__ == '__main__':
  setLogLevel('info')
  testNetwork()
