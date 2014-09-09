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
from vlanhost import VLANHost

class SimpleVlanISPTopo(Topo):

    """ Simple ISP Topology with VLAN support

    linkopts = 1:core, 2:aggregation, 3: edge
    hosts - number of hosts per aggregation switch
        
    1 core router TODO
    1 core switch
    2 aggregation switches
    1 no vlan host connected to each aggregation switch, this is to test vlan
    isolation
    
    Max hosts per aggregation switch = 255 because we use the las 2 HEX digits
    of MAC address for easy debug.

    NOTE: logic has to support setting at least bw and delay parameters for
    each link.
    
    linkopts1- link options between core switch and core router
    linkopts2 - link options between aggregation and core switch
    linkopts3 - link options between aggregation and hosts
    
    """
    
    setLogLevel('info')
    
    def __init__(self, linkopts1={}, linkopts2={}, linkopts3={}, hosts=2,
                 vid=10, cos=0, **opts):
        
        #TODO
        # add cos support, it's not used
        
        """
        
        linkopts1- link options between core switch and core router
        linkopts2 - link options between aggregation and core switch
        linkopts3 - link options between aggregation and hosts
        hosts - numer of hosts per switch between 1 and 255
                                  
                           c0
                  _________|________
                 |         |        |
                 a1       a2       a3
                 |         |        |
                 |    hN+1 -- h2N   |
                 |                  |
               h1--hN         h2N+1 -- h3N
               
        """
        
        # Initialize topology and default options
        Topo.__init__(self, **opts)

        # Base MAC address
        baseMac1 = '00:00:01:00:00:'
        baseMac2 = '00:00:02:00:00:'
        baseMac3 = '00:00:03:00:00:'
        
        # Aux var to count DPID
        dpcount = 1
 
        # Add CORE
        info( '\n*** Adding Core switch\n' )
        core = self.addSwitch('c1', dpid=( "%016x" % dpcount ))
        dpcount += 1

        # Add Agreggation
        info( '\n*** Adding aggregation switches\n' )
        a1 = self.addSwitch('a1', dpid=( "%016x" % dpcount ))
        dpcount += 1
        self.addLink(core, a1, **linkopts2)
        a2 = self.addSwitch('a2', dpid=( "%016x" % dpcount ))
        dpcount += 1
        self.addLink(core, a2, **linkopts2)
        a3 = self.addSwitch('a3', dpid=( "%016x" % dpcount ))
        dpcount += 1
        self.addLink(core, a3, **linkopts2)
        
        # no vlan hosts
        info( '\n*** Adding hosts without VLAN\n' )
        novlan1 = self.addHost(name='nv1', mac='00:00:01:11:11:11',
                              ip='10.11.11.11')
        novlan2 = self.addHost(name='nv2', mac='00:00:02:22:22:22',
                              ip='10.22.22.22')
        novlan3 = self.addHost(name='nv3', mac='00:00:03:33:33:33',
                              ip='10.33.33.33')
        self.addLink(a1, novlan1, **linkopts3)
        self.addLink(a2, novlan2, **linkopts3)
        self.addLink(a3, novlan3, **linkopts3)
            
               
        info( '\n*** Adding VLAN hosts\n' )
        for h in irange(1, hosts):
            hmac1 = baseMac1 + format(h, 'x')
            hmac2 = baseMac2 + format(h, 'x')
            hmac3 = baseMac3 + format(h, 'x')
            hname1 = 'h%s' % str(h)
            hname2 = 'h%s' % str(hosts + h)
            hname3 = 'h%s' % str(hosts * 2 + h)
            host1 = self.addHost(name=hname1, mac=hmac1, cls=VLANHost, vlan=vid)
            host2 = self.addHost(name=hname2, mac=hmac2, cls=VLANHost, vlan=vid)
            host3 = self.addHost(name=hname3, mac=hmac3, cls=VLANHost, vlan=vid)
            self.addLink(a1, host1, **linkopts3)
            self.addLink(a2, host2, **linkopts3)
            self.addLink(a3, host3, **linkopts3)
             
