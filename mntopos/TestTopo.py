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

import sys
import getopt
import argparse
import errno

linkopts1 = {'bw':1000, 'delay':'1ms'}
linkopts2 = {'bw':1000, 'delay':'1ms'}
linkopts3 = {'bw':100, 'delay':'10ms'}

#linkopts1 = {}
#linkopts2 = {}
#linkopts3 = {}

#TODO
# - cos implementation
# - quagga implementation (routerctor.py)
# - Data Center topo with vlan support and all


def main(argv):
    '''
    Script to test Mininet Topologies
    Positional Arguments: NONE
    Optional Arguments:
    remote use remote controller
    ip remote controller ip
    port remote controller tcp port
    vlanid for VLAN topologies, VLAN VID
    vlancos for VLAN topologies, VLAN COS
    fanout for Data Center Topologies, tree fanout
    hosts for ISP Topologies, hosts per aggregation switch
    CustomTopo select topology to test
    '''
    
    parser = argparse.ArgumentParser(description="Wrapper script to initiate " +
                        "Mininet Topologies", add_help=True,
                        epilog="VLANs are supported with topology SISP" +
                        " only. Other topologies will just ignore the setting" +
                        " and will not output any error message.")
    parser.add_argument("--remote",
                        help="Specify a remote controller",
                        action="store_true")
    parser.add_argument("--dhcp",
                        help="Use DHCP Server instead of static ip assignment",
                        action="store_true")
    parser.add_argument("--nat",
                        help="Configure Gateway router to use NATr",
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
    vlanGroup.add_argument("--vlanid",
                        type=int,
                        help="VID value for VLAN Tag (allowed values 2-4096)",
                        #choices=irange(2, 4096),
                        # dont use choises looks bad
                        # validate somewhere else
                        default=0)
    vlanGroup.add_argument("--vlancos",
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
    parser.add_argument("--topo",
                        type=str,
                        help="Custom topology to use",
                        choices=['SISP', 'SDC'],
                        default='SISP')
    args = parser.parse_args()
    
    # Validate VLAN Vid
    if args.vlanid > 4096 :
        print "Allowed VID range is 1 - 4096 (vlan 0 is no vlan)"
        parser.print_help()
        exit(errno.EINVAL)
    
    if args.topo == 'SISP' :
        topo = SimpleISPTopo(linkopts1, linkopts2, linkopts3, hosts=args.hosts,
               vlanid=args.vlanid, vlancos=args.vlancos, dhcp=args.dhcp,
               nat=args.nat, waitConnected=True)
    elif args.topo == 'SDC' :
        topo = SimpleDCTopo(linkopts1, linkopts2, linkopts3, fanout=args.fanout,
               vlanid=args.vlanid, vlancos=args.vlancos, dhcp=args.dhcp,
               nat=args.nat, waitConnected=True)
    
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
    
