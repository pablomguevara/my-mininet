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

class SimpleISPTopo(Topo):

    """ Simple ISP Topology

    linkopts = 1:core, 2:aggregation, 3: edge
    fanout - number of child switch per parent switch
    
    1 core switch
    3 aggregation switches
    
    Max hosts per aggregation switch = 255 because we use the las 2 HEX digits
    of MAC address for easy debug.

    NOTE: logic has to support setting at least bw and delay parameters for
    each link.
    
    linkopts1- link options between core switch and core router
    linkopts2 - link options between aggregation and core switch
    linkopts3 - link options between aggregation and hosts
    
    """
    
    def __init__(self, linkopts1={}, linkopts2={}, linkopts3={}, hosts=2,
        vlanid=0, vlancos=0, nat=False, dhcp=False, visolation=False, 
        gwIp='10.255.255.254', subnet='10.0/8', **opts):
        
        """
        
        linkopts1- link options between core switch and core router
        linkopts2 - link options between aggregation and core switch
        linkopts3 - link options between aggregation and hosts
        hosts - numer of hosts per switch between 1 and 255
        vlanid - sets vlan id for Mininet hosts
        vlancos - sets cos for vlan tagged traffic on Mininet
        dhcp - uses DHCP server for addressing instead of Mininet static ip
        visolation - for VLAN topos, add a couple of no vlan hosts on each sw
        
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
               
        """
        # Print arguments
        info('*** Hosts per switch %s\n' % hosts)
        info('*** VLAN ID %s\n' % vlanid)
        info('*** VLAN COS %s\n' % vlancos)
        
        # Initialize topology and default options
        Topo.__init__(self, **opts)
        
        # Base MAC address
        baseMac1 = '00:00:01:00:00:'
        baseMac2 = '00:00:02:00:00:'
        baseMac3 = '00:00:03:00:00:'
        
        # Aux var to count DPID
        dpcount = 1
        
        # Add CORE
        info( '*** Adding Core switch\n' )
        core = self.addSwitch('c1', dpid=( "%016x" % dpcount ))
        dpcount += 1
        
        # Add Agreggation
        info( '*** Adding aggregation switches\n' )
        a1 = self.addSwitch('a1', dpid=( "%016x" % dpcount ))
        dpcount += 1
        self.addLink(core, a1, **linkopts2)
        a2 = self.addSwitch('a2', dpid=( "%016x" % dpcount ))
        dpcount += 1
        self.addLink(core, a2, **linkopts2)
        a3 = self.addSwitch('a3', dpid=( "%016x" % dpcount ))
        dpcount += 1
        self.addLink(core, a3, **linkopts2)
        
        if dhcp :
            info( '*** Adding hosts with dhcp addressing\n' )
        if vlanid != 0 :
            info( '*** Adding hosts with VLAN ID %s\n' % vlanid )
        else :
            info( '*** Adding hosts\n' )
        
        for h in irange(1, hosts):
            hmac1 = baseMac1 + format(h, 'x')
            hmac2 = baseMac2 + format(h, 'x')
            hmac3 = baseMac3 + format(h, 'x')
            hname1 = 'h%s' % str(h)
            hname2 = 'h%s' % str(hosts + h)
            hname3 = 'h%s' % str(hosts * 2 + h)
            host1 = self.addHost(cls=hostCtor, name=hname1, mac=hmac1,
                vlanid=vlanid, vlancos=vlancos, dhcp=dhcp,
                gwIp=gwIp, subnet=subnet)
            host2 = self.addHost(cls=hostCtor, name=hname2, mac=hmac2,
                vlanid=vlanid, vlancos=vlancos, dhcp=dhcp,
                gwIp=gwIp, subnet=subnet)
            host3 = self.addHost(cls=hostCtor, name=hname3, mac=hmac3,
                vlanid=vlanid, vlancos=vlancos, dhcp=dhcp,
                gwIp=gwIp, subnet=subnet)
            self.addLink(a1, host1, **linkopts3)
            self.addLink(a2, host2, **linkopts3)
            self.addLink(a3, host3, **linkopts3)

        # no vlan hosts
        if vlanid != 0 and visolation == True : 
            info( '*** Adding hosts without VLAN\n' )
            novlan1 = self.addHost(name='nv1', mac='00:00:01:11:11:11',
                gwIp=gwIp, subnet=subnet)
            novlan2 = self.addHost(name='nv2', mac='00:00:02:22:22:22',
                gwIp=gwIp, subnet=subnet)
            novlan3 = self.addHost(name='nv3', mac='00:00:03:33:33:33',
                gwIp=gwIp, subnet=subnet)
            self.addLink(a1, novlan1, **linkopts3)
            self.addLink(a2, novlan2, **linkopts3)
            self.addLink(a3, novlan3, **linkopts3)

