#!/usr/bin/python

from mininet.net import Mininet
from mininet.node import Controller, RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel, info

def int2dpid( dpid ):
   try:
      dpid = hex( dpid )[ 2: ]
      dpid = '0' * ( 16 - len( dpid ) ) + dpid
      return dpid
   except IndexError:
      raise Exception( 'Unable to derive default datapath ID - '
                       'please either specify a dpid or use a '
               'canonical switch name such as s23.' )

def emptyNet():
   "Create a simulated network"

   net = Mininet( controller=lambda a: RemoteController(a, ip='192.168.144.254' ))
   info( '*** Adding controller\n' )
   net.addController( 'c0' )

   info( '*** Adding hosts\n' )
   h1 = net.addHost( 'h1', ip='10.0.0.1' )
   h2 = net.addHost( 'h2', ip='10.0.0.2' )

   info( '*** Adding switches\n' )
   ovs1 = net.addSwitch( 'ovs1', dpid=int2dpid(1), protocols='OpenFlow13', stp_enable='true')
   ovs2 = net.addSwitch( 'ovs2', dpid=int2dpid(2), protocols='OpenFlow13', stp_enable='true')
   ovs3 = net.addSwitch( 'ovs3', dpid=int2dpid(3), protocols='OpenFlow13', stp_enable='true')
   hp1 = net.addSwitch( 'hp1', dpid=int2dpid(11), protocols='OpenFlow13', stp_enable='true')
   hp2 = net.addSwitch( 'hp2', dpid=int2dpid(21), protocols='OpenFlow13', stp_enable='true')

   info( '*** Creating links\n' )
   net.addLink( h1, hp1 )
   net.addLink( h2, hp2 )
   net.addLink( hp1, hp2 )
   net.addLink( hp1, ovs1 )
   net.addLink( hp1, ovs2 )
   net.addLink( ovs1, hp2 )
   net.addLink( ovs2, ovs3 )
   net.addLink( ovs3, hp2 )

   info( '*** Starting network\n')
   net.start()

   info( '*** Running CLI\n' )
   CLI( net )

   info( '*** Stopping network' )
   net.stop()

if __name__ == '__main__':
   setLogLevel( 'info' )
   emptyNet()
