#!/usr/bin/python

"""

This is a class constructor for hosts acting as router
The plan is for this ctor to allow to do static routing with
iptables only.

Pablo M. Guevara <pablomguevara@gmail.com>


"""

from mininet.cli import CLI
from mininet.log import lg, setLogLevel, info, debug
from mininet.node import Node
from mininet.node import Host

DHCP_CONF='$HOME/sdn-project/mntopos/dhcpd-1.conf'

class routerCtor( Host ):
    
    def config( self, nat=False, inetIntf='eth0', subnet='10.0/8',
        vlanid=0, vlancos=0, dhcp=False, **params ):
        
        """
        Configure Start Router implemented with iptables forwarding between 
        Mininet and external network
        
        nat: if True, then NAT
        dhcp: act as dhcp server
        inetIntf: interface for internet access
        subnet: Mininet subnet (default 10.0/8)
        quagga: if true, use quagga
        vlanid: vlanid configuration for Mininet facing interface (0 is no vlanid)
        """
        
        info('*** routerCtor VLAN ', vlanid, '\n')
        debug('*** setting router ip ', params['ip'], '\n')
        debug('*** setting router mac ', params['mac'], '\n')
 
        prefixLen = subnet.split( '/' )[ 1 ]
         
        root = super( Host, self ).config( **params )
                
        # Identify the interface connecting to the mininet network
        localIntf =  self.defaultIntf()
        
        if vlanid == 0 : 
            # assign the host's IP
            self.cmd( 'ifconfig %s inet %s' % ( localIntf, params['ip'] ) )
        else :
            # remove IP from default interface
            self.cmd( 'ifconfig %s inet 0' % localIntf )
            # create VLAN interface 
            self.cmd( 'vconfig add %s %d' % ( localIntf, vlanid ) )
            # assign the host's IP to the VLAN interface
            self.cmd( 'ifconfig %s.%d inet %s' % ( localIntf, vlanid, params['ip'] ) )
            # update the intf name and host's intf map
            newName = '%s.%d' % ( localIntf, vlanid )
            # update the (Mininet) interface to refer to VLAN interface name
            localIntf.name = newName
            # add VLAN interface to host's name to intf map
            self.nameToIntf[ newName ] = localIntf
        
        # Flush any currently active rules
        self.cmd( 'iptables -F' )
        self.cmd( 'iptables -t nat -F' )
        
        # Create default entries for unmatched traffic
        self.cmd( 'iptables -P INPUT ACCEPT' )
        self.cmd( 'iptables -P OUTPUT ACCEPT' )
        self.cmd( 'iptables -P FORWARD ACCEPT' )
        
        # Configure iptables router
        self.cmd( 'iptables -I FORWARD -i', localIntf, '-d', subnet, '-j DROP' )
        self.cmd( 'iptables -A FORWARD -i', localIntf, '-s', subnet, '-j ACCEPT' )
        self.cmd( 'iptables -A FORWARD -i', inetIntf, '-d', subnet, '-j ACCEPT' ) 
        if nat :
            # Configure NAT
            self.cmd( 'iptables -t nat -A POSTROUTING -o ', inetIntf, '-j MASQUERADE' )
        
        # Instruct the kernel to perform forwarding
        self.cmd( 'sysctl net.ipv4.ip_forward=1' )
        
        if dhcp :
            # Set config and Start DHCP Server process
            # Kill any running DHCP
            self.cmd( 'kill $(echo $(cat /var/run/dhcpd.pid))' )
            # Deploy the right DHCP configuration for the example
            self.cmd( 'cp /etc/dhcp/dhcpd.conf /etc/dhcp/dhcpd.conf.bak' )
            self.cmd( 'cp ', DHCP_CONF, '/etc/dhcp/dhcpd.conf' )
            # Configure interface to listen DHCP
            self.cmd( 'cp /etc/default/isc-dhcp-server /etc/default/isc-dhcp-server.bak' )
            self.cmd( 'echo "INTERFACES=\"%s\"" > /etc/default/isc-dhcp-server' % localIntf )
            # Start DHCP
            self.cmd( 'dhcpd &' )
 
        return root

    def terminate( self ):
        # Just flush and add policies, keep it simple but unsecure
        # Flush any currently active rules
        self.cmd( 'iptables -F' )
        self.cmd( 'iptables -t nat -F' )

        # Create default entries for unmatched traffic
        self.cmd( 'iptables -P INPUT ACCEPT' )
        self.cmd( 'iptables -P OUTPUT ACCEPT' )
        self.cmd( 'iptables -P FORWARD ACCEPT' )

        # Instruct the kernel to stop forwarding
        self.cmd( 'sysctl net.ipv4.ip_forward=0' )

        # Terminate DHCP
        self.cmd( 'kill $(echo $(cat /var/run/dhcpd.pid))' )

        # Restore files
        self.cmd('cp /etc/dhcp/dhcpd.conf.bak /etc/dhcp/dhcpd.conf')
        self.cmd('cp /etc/default/isc-dhcp-server.bak /etc/default/isc-dhcp-server')        

        # Terminate
        super( Host, self ).terminate()

