#!/usr/bin/python
'''

Pablo M. Guevara <pablomguevara@gmail.com>

'''

from mininet.topo import Topo
from mininet.util import irange
from mininet.link import TCLink
from mininet.link import Intf
from mininet.log import setLogLevel, info, debug
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.node import Host
from mininet.node import Node
from hostctor import hostCtor

class OneSwitchTopo(Topo):

    """ Simple Topology with One switch only

    This is the equivalent of standard mn "single", but with vlan support and other stuff.

    linkopts = 1:core, 2:aggregation, 3: edge
    hosts - number of hosts on the switch
    
    Max hosts per aggregation switch = 250 because we use the las 2 HEX digits
    of MAC address for easy debug.

    NOTE: logic has to support setting at least bw and delay parameters for
    each link.
    
    linkopts1- link options between core switch and core router
    linkopts2 - link options between aggregation and core switch
    linkopts3 - link options between aggregation and hosts
    
    """
    
    def __init__(self, linkopts1={}, linkopts2={}, linkopts3={}, hosts=2,
        vlanid=0, vlancos=0, nat=False, dhcp=None, visolation=False, 
        gwIp='10.255.255.254', subnet='10.0/8', **opts):
        
        """
        
        linkopts1- link options between single witch and core router
        linkopts2 - link options between single switch and hosts
        linkopts3 - not used
        hosts - numer of hosts between 1 and 250
        vlanid - sets vlan id for Mininet hosts
        vlancos - sets cos for vlan tagged traffic on Mininet
        dhcp - uses DHCP server for addressing instead of Mininet static ip
        visolation - add a couple of no vlan hosts on each sw
        
                          eth0
                           |                            
                           |                           
                  _________|________
                 |         |        |
                 a1       a2       a3
                 |         |        |
                 |    hN+1 -- h2N   |
                 |                  |
               h1--hN         h2N+1 -- h3N
        
        dhcp argument values are None or dhcp. If dhcp=None we use static IP;
        if dhcp=dhcp hosts will try to get ip from the network
               
        """
        # Print arguments
        info('*** Hosts per switch %s\n' % hosts)
        info('*** VLAN ID %s\n' % vlanid)
        info('*** VLAN COS %s\n' % vlancos)
        
        # Initialize topology and default options
        Topo.__init__(self, **opts)
        
        # Base MAC address
        baseMac1 = '00:00:01:00:00:'
        
        # Add Single Switch
        info( '*** Adding single switch\n' )
        core = self.addSwitch('c1', dpid=( "%016x" % 1 ))
        
        if dhcp :
            info( '*** Adding hosts with dhcp addressing\n' )
        if vlanid != 0 :
            info( '*** Adding hosts with VLAN ID %s\n' % vlanid )
        else :
            info( '*** Adding hosts\n' )
        
        for h in irange(1, hosts):
            hmac1 = baseMac1 + format(h, 'x')
            hname1 = 'h%s' % str(h)
            host1 = self.addHost(cls=hostCtor, name=hname1, mac=hmac1,
                vlanid=vlanid, vlancos=vlancos, dhcp=dhcp,
                gwIp=gwIp, subnet=subnet)
            self.addLink(core, host1, **linkopts3)
        
        # no vlan hosts
        if vlanid != 0 and visolation == True :
            info( '*** Adding hosts without VLAN to verify isolation\n' )
            novlan1 = self.addHost(name='nv1', mac='00:00:01:11:11:11',
                gwIp=gwIp, subnet=subnet)
            novlan2 = self.addHost(name='nv2', mac='00:00:02:22:22:22',
                gwIp=gwIp, subnet=subnet)
            self.addLink(core, novlan1, **linkopts3)
            self.addLink(core, novlan2, **linkopts3)

