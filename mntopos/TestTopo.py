#!/usr/bin/python
'''

Pablo M. Guevara <pablomguevara@gmail.com>

'''

from mininet.net import Mininet
from mininet.util import dumpNodeConnections
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.node import RemoteController

from SimpleDCTopo import *
from SimpleISPTopo import *
from SimpleVlanISPTopo import *

import sys
import getopt
import argparse
import errno

#linkopts1 = {'bw':50, 'delay':'5ms'}
#linkopts2 = {'bw':30, 'delay':'10ms'}
#linkopts3 = {'bw':10, 'delay':'15ms'}

linkopts1 = {}
linkopts2 = {}
linkopts3 = {}

def main(argv):
    '''
    Script to test Mininet Topologies
    Positional Arguments: NONE
    Optional Arguments:
    remote use remote controller
    ip remote controller ip
    port remote controller tcp port
    vid for VLAN topologies, VLAN VID
    cos for VLAN topologies, VLAN COS
    fanout for Data Center Topologies, tree fanout
    hosts for ISP Topologies, hosts per aggregation switch
    CustomTopo select topology to test
    '''
    
    parser = argparse.ArgumentParser(description="Simple script to initiate " +
                        "Mininet Topologies", add_help=True,
                        epilog="VLANs are supported with topology SISPVlan" +
                        " only. Other topologies will just ignore the setting" +
                        " and will not output any error message.")
    parser.add_argument("--remote",
                        help="Specify a remote controller",
                        action="store_true")
    controllerGroup = parser.add_argument_group('controllerGroup',
                        'Arguments for remote controller')
    controllerGroup.add_argument("--ip",
                        help="Specify ip address for remote controller",
                        default="127.0.0.1")
    controllerGroup.add_argument("--port",
                        type=int,
                        help="Specify tcp port for remote controller",
                        default=6633)
    vlanGroup = parser.add_argument_group('VlanGroup',
                        'Vlan related arguments')
    vlanGroup.add_argument("--vid",
                        type=int,
                        help="VID value for VLAN Tag (allowed values 2-4096)",
                        #choices=irange(2, 4096),
                        # dont use choises looks bad
                        # validate somewhere else
                        default=10)
    vlanGroup.add_argument("--cos",
                        type=int,
                        help="COS value for VLAN Tag",
                        choices=irange(0, 7),
                        default=0)
    group1 = parser.add_mutually_exclusive_group()
    group1.add_argument("--fanout",
                        type=int,
                        help="Fanout for DC-like topologies",
                        default=2)
    group1.add_argument("--hosts",
                        type=int,
                        help="Number of hosts per aggregation switch for" +
                        " ISP-like topologies",
                        default=2)
    parser.add_argument("--CustomTopo",
                        type=str,
                        help="Custom topology to use",
                        choices=['SISP', 'SISPVlan', 'SDC'],
                        default='SISP')
    args = parser.parse_args()
    
    # Validate VLAN Vid
    if args.vid < 2 or args.vid > 4096 :
        print "Allowed VID range is 2 - 4096"
        parser.print_help()
        exit(errno.EINVAL)
    
    if args.CustomTopo == 'SISP' :
        topo = SimpleISPTopo(linkopts1, linkopts2, linkopts3, hosts=args.hosts)
    elif args.CustomTopo == 'SISPVlan' :
        topo = SimpleVlanISPTopo(linkopts1, linkopts2, linkopts3, hosts=args.hosts,
               vid=args.vid, cos=args.cos)
    elif args.CustomTopo == 'SDC' :
        topo = SimpleDCTopo(linkopts1, linkopts2, linkopts3, fanout=args.fanout)
    
    if args.remote :
        net = Mininet(topo=topo,
              link=TCLink,
              controller=lambda a: RemoteController(a, ip=args.ip, port=args.port )
              )
    else:
        net = Mininet(topo=topo, link=TCLink)
    
    net.start()
    dumpNodeConnections(net.hosts)
    CLI(net)
    net.stop()

if __name__ == "__main__":
   main(sys.argv[1:])
   
