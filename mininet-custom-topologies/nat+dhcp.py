#!/usr/bin/python

"""
Example to create a Mininet topology and connect it to the internet via NAT
through eth0 on the host.

Glen Gibb, February 2011

(slight modifications by BL, 5/13)

Modified by Pablo Guevara <pablomguevara@gmail.com>

Script to test mininet topologies with dhcp and nat
Creates a router for internet access that will forward to eth0
Starts DHCP server with configuration file on var DHCP_CONF
DHCP sever is configured to listed on dhcp-eth0 interface
DHCP subnet is the standar Mininet 10.0.0.0/8, this could be changed
Default gateway is 10.0.0.254
The router/root node acting as gateway for hosts also NATs using IP tables
masquerade
DNS server is my internal router 192.168.143.254
"""

# DHCP configuration file
#
# /etc/dhcp/dhcpd.conf
#
#ddns-update-style none;
#option domain-name "argenta.net.ar";
#option domain-name-servers 192.168.143.254;
#default-lease-time 600;
#max-lease-time 7200;
#authoritative;
#log-facility local7;
#subnet 10.0.0.0 netmask 255.255.255.0 {
#     # specify default gateway
#     option routers 10.0.0.254;
#     # specify subnet-mask
#     option subnet-mask 255.255.255.0;
#     # specify the range of leased IP address
#     range dynamic-bootp 10.0.0.1 10.0.0.200;
#}


from mininet.cli import CLI
from mininet.log import lg
from mininet.node import Node
from mininet.topolib import TreeNet
from mininet.log import setLogLevel, info, error
from mininet.node import RemoteController
from mininet.net import Mininet

DHCP_CONF='$HOME/sdn-project/mininet-custom-topologies/dhcpd-1.conf'

#################################
def startNAT( root, inetIntf='eth0', subnet='10.0/8' ):
    """Start NAT/forwarding between Mininet and external network
    root: node to access iptables from
    inetIntf: interface for internet access
    subnet: Mininet subnet (default 10.0/8)="""

    # Identify the interface connecting to the mininet network
    localIntf =  root.defaultIntf()

    # Flush any currently active rules
    root.cmd( 'iptables -F' )
    root.cmd( 'iptables -t nat -F' )

    # Create default entries for unmatched traffic
    root.cmd( 'iptables -P INPUT ACCEPT' )
    root.cmd( 'iptables -P OUTPUT ACCEPT' )
    root.cmd( 'iptables -P FORWARD DROP' )

    # Configure NAT
    #root.cmd( 'iptables -I FORWARD -i', localIntf, '-d', subnet, '-j DROP' )
    root.cmd( 'iptables -A FORWARD -i', localIntf, '-s', subnet, '-j ACCEPT' )
    root.cmd( 'iptables -A FORWARD -i', inetIntf, '-d', subnet, '-j ACCEPT' )
    root.cmd( 'iptables -t nat -A POSTROUTING -o ', inetIntf, '-j MASQUERADE' )

    # Instruct the kernel to perform forwarding
    root.cmd( 'sysctl net.ipv4.ip_forward=1' )

def startDHCP( dhcp ):
    """ Config and Start DHCP Server process to assign addresses"""
    
    # Kill any running DHCP
    dhcp.cmd( 'kill $(echo $(cat /var/run/dhcpd.pid))' )
    
    # Deploy the right DHCP configuration for the example
    dhcp.cmd('cp /etc/dhcp/dhcpd.conf /etc/dhcp/dhcpd.conf.bak')
    dhcp.cmd('cp ', DHCP_CONF, '/etc/dhcp/dhcpd.conf')
        
    # Configure interface to listen DHCP
    dhcp.cmd('cp /etc/default/isc-dhcp-server /etc/default/isc-dhcp-server.bak')
    dhcp.cmd('echo "INTERFACES=\"dhcp-eth0\"" > /etc/default/isc-dhcp-server')
    
    # Start DHCP
    dhcp.cmd( 'dhcpd &' )  

def stopDHCP( dhcp ):
    """Stop DHCP Process"""
    
    # Stop DHCP
    dhcp.cmd( 'kill $(echo $(cat /var/run/dhcpd.pid))' )
    
    # Restore files
    dhcp.cmd('cp /etc/dhcp/dhcpd.conf.bak /etc/dhcp/dhcpd.conf')
    dhcp.cmd('cp /etc/default/isc-dhcp-server.bak /etc/default/isc-dhcp-server')
    
def stopNAT( root ):
    """Stop NAT/forwarding between Mininet and external network"""
    # Flush any currently active rules
    root.cmd( 'iptables -F' )
    root.cmd( 'iptables -t nat -F' )

    # Instruct the kernel to stop forwarding
    root.cmd( 'sysctl net.ipv4.ip_forward=0' )

def fixNetworkManager( root, intf ):
    """Prevent network-manager from messing with our interface,
       by specifying manual configuration in /etc/network/interfaces
       root: a node in the root namespace (for running commands)
       intf: interface name"""
    cfile = '/etc/network/interfaces'
    line = '\niface %s inet manual\n' % intf
    config = open( cfile ).read()
    if line not in config:
        print '*** Adding', line.strip(), 'to', cfile
        with open( cfile, 'a' ) as f:
            f.write( line )
        # Probably need to restart network-manager to be safe -
        # hopefully this won't disconnect you
        root.cmd( 'service network-manager restart' )

def addNode( network, nodename, switch='s1', ipaddr='10.254', subnet='10.0/8',
    inNs=False ):
    """Add Generic Node
       switch: switch to connect dhcp
       ipaddr: address for interface in dhcp
       subnet: Mininet subnet
       inNs: False, the node to be added is on root namespace"""
    
    switch = network.get( switch )
    prefixLen = subnet.split( '/' )[ 1 ]

    # Create a node
    N = Node( name=nodename, inNamespace=inNs )   
    
    # Prevent network-manager from interfering with our interface 
    fixNetworkManager( N, nodename + '-eth0' )

    # Create link between dhcp NS and switch
    link = network.addLink( N, switch )
    link.intf1.setIP( ipaddr, prefixLen )
    
    return N

def connectToInternet( network, root, dhcp ):
    """Connect the network to the internet
    root: the root router
    dhcp: the dhcp server"""
    
    # Start network that now includes link to root/dhcp namespace
    network.start()
    
    # Start DHCP
    startDHCP( dhcp)
    
    # Start NAT and establish forwarding
    startNAT( root )

    # Start DHCP Clients for hosts
    for host in network.hosts:
        host.cmd( 'ip route flush root 0/0' )
        host.cmd( 'dhclient', host.defaultIntf(), '&' )
        
def stopNetwork( network, root, dhcp ):
    stopDHCP( dhcp )
    stopNAT( root )
    network.stop()
    
def testNetwork():
    info( '*** Creating network\n' )
    
    # add remote controller
    net = Mininet( controller=lambda a: RemoteController(a, ip='127.0.0.1', port=6633 ))
    net.addController('c0')
    
    # add switch
    s1 = net.addSwitch('s1')
    
    # add hosts
    h1 = net.addHost('h1', ip='0.0.0.0')
    h2 = net.addHost('h2', ip='0.0.0.0')
    
    # add links
    net.addLink(h1,s1)
    net.addLink(h2,s1)
      
    # start network
    net.start()
    
    # Add Router
    root = addNode( net, 'root' )
    
    # Add DHCP
    dhcp = addNode( net, 'dhcp', ipaddr='10.253' )
    
    # Configure and start NATted connectivity
    connectToInternet( net, root, dhcp )
    
    print "*** Hosts are running and should have internet connectivity"
    print "*** Type 'exit' or control-D to shut down network"
    
    # Start Xterm for all hosts
    net.startTerms()
    
    CLI( net )
    
    # Stop Network
    stopNetwork ( net, root, dhcp )

if __name__ == '__main__':
    lg.setLogLevel( 'info')
    testNetwork()


