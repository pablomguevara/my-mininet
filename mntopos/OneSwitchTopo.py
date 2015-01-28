#!/usr/bin/python
'''

Pablo M. Guevara <pablomguevara@gmail.com>

'''

from mininet.topo import Topo
from mininet.util import irange
from mininet.link import TCLink
from mininet.log import setLogLevel, info, debug
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.node import Host
from mininet.node import Node
from routerctor import routerCtor
from hostctor import hostCtor
from dhcpctor import dhcpCtor

class OneSwitchTopo(Topo):

    """ Simple Topology with One switch only

    This is the equivalent of standard mn "single", but with router, dhcp
    and custom constructors.

    linkopts = 1:core, 2:aggregation, 3: edge
    hosts - number of hosts on the switch
    
    1 core router that optionaly acts as dhcp server
    1 core switch
    N hosts
    
    The core router, the gw uses ip 10.0.0.1.
    The current implementation let's Mininet assign the gw router ip
    automatically because gw is a host on root namespace. This is the first
    host. All other hosts, from 2 to N, should have gw as default route
    
    If the dhcp option is enabled, the script adds a dhcp server to the gw node
    10.0.0.1 and the server assigns IPs for hosts on the subnet.
            
    Max hosts per aggregation switch = 250 because we use the las 2 HEX digits
    of MAC address for easy debug.

    NOTE: logic has to support setting at least bw and delay parameters for
    each link.
    
    linkopts1- link options between core switch and core router
    linkopts2 - link options between aggregation and core switch
    linkopts3 - link options between aggregation and hosts
    
    """
    
    setLogLevel('info')
    #setLogLevel('debug')
    
    def __init__(self, linkopts1={}, linkopts2={}, linkopts3={}, hosts=2,
        vlanid=0, vlancos=0, nat=False, dhcp=None, **opts):
        
        """
        
        linkopts1- link options between single witch and core router
        linkopts2 - link options between single switch and hosts
        linkopts3 - not used
        hosts - numer of hosts between 1 and 250
        vlanid - sets vlan id for Mininet hosts
        vlancos - sets cos for vlan tagged traffic on Mininet
        nat - enabled NAT on the gw router
        dhcp - uses DHCP server for addressing instead of Mininet static ip
        
                          gw/dhcp
                           |                            
                           c0
                  _________|________
                 |         |        |
                 a1       a2       a3
                 |         |        |
                 |    hN+1 -- h2N   |
                 |                  |
               h1--hN         h2N+1 -- h3N
        
        dhcp argument values are None, dhcp and gw. If dhcp=None we use static IP;
        if dhcp=dhcp we create a new node with hostname dhcp; if dhcp=gw we use
        the gw node as router and dhcp.
               
        """
        # Print arguments
        info('*** Hosts per switch %s\n' % hosts)
        info('*** VLAN ID %s\n' % vlanid)
        info('*** VLAN COS %s\n' % vlancos)
        
        # Initialize topology and default options
        Topo.__init__(self, **opts)
        
        # The gw router IP address and mac
        gwMac='00:00:00:bb:bb:bb'
        gwIp='10.0.0.1'
        
        # Base MAC address
        baseMac1 = '00:00:01:00:00:'
        
        # Add Single Switch
        info( '*** Adding single switch\n' )
        core = self.addSwitch('c1', dpid=( "%016x" % 1 ))
 
        # Add gateway and dhcp
        if dhcp == 'gw':
            dhcpMac=gwMac
            dhcpMac=gwIp
            dhcpBln=True
            info( '*** Adding gateway router node with DHCP server\n' )
            gw = self.addHost(name='gw', cls=routerCtor, inNamespace=False,
                              ip=gwIp, vlanid=vlanid, vlancos=vlancos, nat=nat,
                              mac=gwMac, dhcp=True)
            self.addLink(core, gw, **linkopts1)
        if dhcp == 'dhcp':
            dhcpIp='10.0.0.254'
            dhcpMac='00:00:00:aa:aa:aa'
            dhcpBln=True
            info( '*** Adding gateway router node without DHCP server\n' )
            gw = self.addHost(name='gw', cls=routerCtor, inNamespace=False,
                              ip=gwIp, vlanid=vlanid, vlancos=vlancos, nat=nat,
                              mac=gwMac, dhcp=False)
            self.addLink(core, gw, **linkopts1)
            info( '*** Adding DHCP server node\n' )
            dhcp = self.addHost(name='dhcp', cls=dhcpCtor, inNamespace=False,
                                dhcpIp=dhcpIp, vlanid=vlanid, vlancos=vlancos,
                                mac=dhcpMac )
            self.addLink(core, dhcp)
        else:
            dhcpIp=None
            dhcpMac=None
            dhcpBln=False
            info( '*** Adding gateway router node for static addressing\n' )
            gw = self.addHost(name='gw', cls=routerCtor, inNamespace=False,
                              ip=gwIp, vlanid=vlanid, vlancos=vlancos, nat=nat,
                              mac=gwMac, dhcp=False)
            self.addLink(core, gw, **linkopts1)
         
        if dhcpBln :
            info( '*** Adding hosts with dhcp addressing\n' )
        if nat :
            info( '*** Adding router with NAT enabled\n' )
        if vlanid != 0 :
            info( '*** Adding hosts with VLAN ID %s\n' % vlanid )
        else :
            info( '*** Adding hosts\n' )
        
        for h in irange(2, hosts+1):
            hmac1 = baseMac1 + format(h, 'x')
            hname1 = 'h%s' % str(h)
            host1 = self.addHost(cls=hostCtor, name=hname1, mac=hmac1,
                vlanid=vlanid, vlancos=vlancos, dhcp=dhcp)
            self.addLink(a1, host1, **linkopts3)
        
        # no vlan hosts
        if vlanid != 0 :
            info( '*** Adding hosts without VLAN to verify isolation\n' )
            novlan1 = self.addHost(name='nv1', mac='00:00:01:11:11:11',
                                   ip='10.11.11.11')
            novlan2 = self.addHost(name='nv2', mac='00:00:02:22:22:22',
                                   ip='10.22.22.22')
            self.addLink(c1, novlan1, **linkopts3)
            self.addLink(c1, novlan2, **linkopts3)

