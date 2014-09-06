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

class SimpleDCTopo(Topo):

    """ Simple Data Center Topology"

    linkopts = 1:core, 2:aggregation, 3: edge
    fanout - number of child switch per parent switch
    
    Max hosts = 255 because we use the las 2 HEX digits of MAC address for
    easy debug.

    NOTE: logic has to support setting at least bw and delay parameters for
    each link.
    """
    
    setLogLevel('info')
    
    def __init__(self, linkopts1={}, linkopts2={}, linkopts3={}, fanout=2, **opts):

        # Initialize topology and default options
        Topo.__init__(self, **opts)

        # Base MAC address
        baseMac = '00:00:00:00:00:'
        
        # Aux variables to count switches and hosts used to assign names
        acount = 1
        ecount = 1
        hcount = 1

        # Add CORE
        core = self.addSwitch('c1')

        # Add Agreggation
        for i in irange(1, fanout):
            aname = ('a%s' % str(acount))
            AggSwitch = self.addSwitch(name=aname)
            self.addLink(core, AggSwitch, **linkopts1)
            acount += 1
            for j in irange(1, fanout):
                ename = ('e%s' % str(ecount))
                EdgeSwitch = self.addSwitch(name=ename)
                self.addLink(AggSwitch, EdgeSwitch, **linkopts2)
                ecount += 1
                for k in irange(1, fanout):
                    hmac = baseMac + format(hcount, 'x')	
                    hname= ('h%s' % str(hcount))
                    host = self.addHost(name=hname, mac=hmac)
                    self.addLink(EdgeSwitch, host, **linkopts3)
                    hcount += 1

