#!/usr/bin/python
'''
This script creates topologies to be used with ONOS

Pablo M. Guevara <pablomguevara@gmail.com>

'''

from mininet.net import Mininet
from mininet.util import dumpNodeConnections
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.node import RemoteController
from mininet.node import Host
from mininet.node import Node

from SimpleDCTopo import *
from SimpleISPTopo import *
from OneSwitchTopo import *
from smartformatter import *
from routerctor import routerCtor 

import sys
import getopt
import argparse
import errno

#linkopts1 = {'bw':1000, 'delay':'1ms'}
#linkopts2 = {'bw':1000, 'delay':'1ms'}
#linkopts3 = {'bw':100, 'delay':'10ms'}

linkopts1 = {}
linkopts2 = {}
linkopts3 = {}

# ROUTER VARS
# TODO move this to args
# The gw router IP address and mac
gwMac='00:00:00:aa:aa:aa'
gwIp='10.255.255.254'

#TODO
# - cos implementation
# - Data Center topo with vlan support and all

def main(argv):

    '''
    Script to test Mininet Topologies
    Positional Arguments: NONE
    Optional Arguments:
    
    # CONTROLLER
    This scripts accepts 1) local Mininet default 2) Controller 1
    3) Controller 2
    if both controllers are provided both ip addresses are required
    if only one controller is provided, then no ip means localhost
    if port is emtpy, asume standard port

    # VLAN
    vlanid for VLAN topologies, VLAN VID
    vlancos for VLAN topologies, VLAN COS
    
    # HOST COUNT
    fanout for Data Center Topologies, tree fanout
    hosts for ISP Topologies, hosts per aggregation switch
    
    # TOPOLOGY
    CustomTopo select topology to test

    # ROUTER
    Optionally, we can install a router on top of the core switch
    Router supports nat and dhcp server each enabled with idividual args
    '''
    
    parser = argparse.ArgumentParser(description="Wrapper script to initiate " +
                        "Mininet Topologies", add_help=True,
                        epilog="VLANs are supported with topology SISP and OS" +
                        " only. Other topologies will just ignore the setting" +
                        " and will not output any error message.",
                        formatter_class=SmartFormatter)
    parser.add_argument("--remote",
                        help="Specify a remote controller",
                        action="store_true")
    
    parser.add_argument("--dhcp",
                        help="R|Use DHCP Server instead of static ip assignment" +
                             " for mininet hosts.",
                        action="store_true")

    routerGroup = parser.add_mutually_exclusive_group()
    routerGroup.add_argument("--router",
                             help="R|Install an iptables based router",
                             action="store_true")
    routerGroup.add_argument("--router_nat",
                             help="R|Install an iptables based router with nat enabled",
                             action="store_true")
    routerGroup.add_argument("--router_dhcp",
                             help="R|Install an iptables based router with dhcp server" +
                                  " enabled",
                             action="store_true")
    routerGroup.add_argument("--router_dhcp_nat",
                             help="R|Install an iptables based router with nat enabled",
                             action="store_true")

    controllerGroup = parser.add_argument_group('controllerGroup',
                        'Arguments for remote controller')
    controllerGroup.add_argument("--cluster",
                        help="Specify if running controllers on cluster (supports 2 controllers only)",
                        action="store_true")
    controllerGroup.add_argument("--ip1",
                        help="Specify ip address for the first remote controller",
                        default="127.0.0.1")
    controllerGroup.add_argument("--port1",
                        type=int,
                        help="Specify tcp port for the first remote controller",
                        default=6633)
    controllerGroup.add_argument("--ip2",
                        help="Specify ip address for the second remote controller",
                        default="127.0.0.1")
    controllerGroup.add_argument("--port2",
                        type=int,
                        help="Specify tcp port for the second remote controller",
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
                        help="R|Number of hosts per aggregation switch for" +
                        " ISP-like topologies",
                        default=2)

    parser.add_argument("--topo",
                        type=str,
                        help="Custom topology to use",
                        choices=['SISP', 'SDC', 'OS'],
                        default='SISP')

    parser.add_argument("--log",
                        type=str,
                        help="Mininet Log level",
                        choices=['info', 'debug'],
                        default='info')

    parser.add_argument("--iface",
                        type=str,
                        help="R|Interface for upstream connectivity on core switch. \n" +
                        "If this is a physical interface it normally works. If on the \n" +
                        "other hand this is a virtual interface (like one connecting \n"
                        "a hypervisor the requirement for it to work is to add this \n" +
                        "interface to a Linux bridge or similar. Examples known to work:\n\n" +
                        "Ryu: add Linux Bridge br0 and add eth0 to it. Then use eth0 for \n" +
                        "this argument\n" +
                        "ONOS: this controller is more complicated 1) add Linux bridge\n" +
                        "2) add veth pair veth0 and veth1 2) add eth0 (the interface that \n" +
                        "communicates with the outside world) and veth0 to the bridge. Then \n" +
                        "use veth1 as argument to Mininet\n\n" +
                        "Ryu example:\n" +
                        "brctl addbr br0\n" +
                        "brctl addif br0 eth0\n" +
                        "Make sure eth0 has no IP, if an IP is needed, add it o br0\n\n" +
                        "ONOS example:\n" +
                        "brctl addbr br0" +
                        "brctl addif br0 eth0\n" +
                        "ip link add veth0 type veth peer name veth1\n" +
                        "ifconfig veth0 up\n" +
                        "ifconfig veth1 up\n" +
                        "ip link set dev veth0 up\n" +
                        "ip link set dev veth1 up\n" +
                        "IMPORTANT: if used with the iptables router this is the internet\n" +
                        "interface.",
                        default='eth0')
    
    args = parser.parse_args()

    # PROCESS ARGUMENTS
    
    # Validate VLAN Vid
    if args.vlanid > 4096 :
        print "Allowed VID range is 1 - 4096 (vlan 0 is no vlan)"
        parser.print_help()
        exit(errno.EINVAL)
    
    # This is added here to avoid inconsistency. If dhcp option is set on
    # router args, then activate dhcp argument for hosts
    if args.router_dhcp or args.router_dhcp_nat :
        args.dhcp = True
     
    # TOPOLOGY 
    if args.topo == 'SISP' :
        topo = SimpleISPTopo(linkopts1, linkopts2, linkopts3, hosts=args.hosts,
               vlanid=args.vlanid, vlancos=args.vlancos, dhcp=args.dhcp,
               waitConnected=True)
    elif args.topo == 'SDC' :
        topo = SimpleDCTopo(linkopts1, linkopts2, linkopts3, fanout=args.fanout,
               vlanid=args.vlanid, vlancos=args.vlancos, dhcp=args.dhcp,
               waitConnected=True)
    elif args.topo == 'OS' :
        topo = OneSwitchTopo(linkopts1, linkopts2, linkopts3, fanout=args.hosts,
               vlanid=args.vlanid, vlancos=args.vlancos, dhcp=args.dhcp,
               waitConnected=True)
    
    # LOGGING
    if args.log == "info" :
        setLogLevel('info')
    else :
        setLogLevel('debug')    
    
    # CONTROLLER
    if args.remote :
        if args.cluster:
            net = Mininet(topo=topo, link=TCLink, controller=RemoteController)
            c1 = net.addController( 'ctrl1', ip=args.ip1, port=args.port1 )
            c2 = net.addController( 'ctrl2', ip=args.ip2, port=args.port2 )
        else :
            net = Mininet(topo=topo,
                  link=TCLink,
                  controller=lambda a: RemoteController(a, ip=args.ip, port=args.port )
                  )
    else:
        net = Mininet(topo=topo, link=TCLink)
    
    # GET THE CORE SWITCH
    # this is used for upstream and router
    # TODO, find a better way to define the switch, specify the switch name "c1"
    # note that core is 0 for OS topo and 3 for all other topos
    if args.topo == "OS" :
        switch = net.switches[ 0 ]
    else :
        switch = net.switches[ 3 ]
        debug('*** Switches ' , net.switches, '\n') 
    
    # ROUTER
    if args.router :
        info( '*** Adding gateway router node for static addressing\n' )
        gw = topo.addHost(cls=routerCtor, inNamespace=False, name='gw',
                         ip=gwIp, vlanid=args.vlanid, vlancos=args.vlancos, nat=False,
                         mac=gwMac, dhcp=False, inetIntf=args.iface)
        info( '*** Adding gateway router link to core switch\n' )
        topo.addLink('c1', gw, **linkopts1)
    elif args.router_nat :
        # ROUTER + NAT
        info( '*** Adding gateway router node for static addressing and nat\n' )
        gw = topo.addHost(cls=routerCtor, inNamespace=False, name='gw',
                         ip=gwIp, vlanid=args.vlanid, vlancos=args.vlancos, nat=True,
                         mac=gwMac, dhcp=False, inetIntf=args.iface)
        topo.addLink('c1', gw, **linkopts1)
    elif args.router_dhcp :
        # ROUTER + DHCP
        info( '*** Adding gateway router node with DHCP server\n' )
        gw = topo.addHost(cls=routerCtor, inNamespace=False, name='gw',
                         ip=gwIp, vlanid=args.vlanid, vlancos=args.vlancos, nat=False,
                         mac=gwMac, dhcp=True, inetIntf=args.iface)
        topo.addLink('c1', gw, **linkopts1)
    elif args.router_dhcp_nat :
        # ROUTER + DHCP + NAT
        info( '*** Adding gateway router node with DHCP server and nat\n' )
        gw = topo.addHost(cls=routerCtor, inNamespace=False, name='gw',
                         ip=gwIp, vlanid=args.vlanid, vlancos=args.vlancos, nat=True,
                         mac=gwMac, dhcp=True, inetIntf=args.iface)
        topo.addLink('c1', gw, **linkopts1)
    else :
        # THERE IS NO ROUTER
        # INTERFACE
        # Add interface for upstream conectivity
        info( '*** Adding hardware interface', args.iface , 'to switch',
              switch.name, '\n' )
        _intf = Intf( args.iface , node=switch )

    # CONTROLLER
    if args.remote :
        if args.cluster:
            net = Mininet(topo=topo, link=TCLink, controller=RemoteController)
            c1 = net.addController( 'ctrl1', ip=args.ip1, port=args.port1 )
            c2 = net.addController( 'ctrl2', ip=args.ip2, port=args.port2 )
        else :
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
    
