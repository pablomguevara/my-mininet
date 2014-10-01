#!/usr/bin/python

"""

This is a class constructor for hosts acting as dhcp server using isc dhcp
server

Pablo M. Guevara <pablomguevara@gmail.com>


"""

from mininet.cli import CLI
from mininet.log import lg, setLogLevel, info, debug
from mininet.node import Node
from mininet.node import Host

DHCP_CONF='$HOME/sdn-project/mininet-custom-topologies/dhcpd-1.conf'

class dhcpCtor( Host ):
    
    setLogLevel('info')
    
    def config( self, subnet='10.0/8', vlanid=0, vlancos=0, dhcpIp='10.0.0.254',
        **params ):
        
        """
        Configure DHCP Server
        
        subnet: Mininet subnet (default 10.0/8)
        vlanid: vlanid configuration for Mininet facing interface (0 is no vlanid)
        """
        
        info('*** dhcoCtor VLAN %s\n' % vlanid)
         
        prefixLen = subnet.split( '/' )[ 1 ]
        
        dhcp = super( Host, self ).config( **params )
                
        # Identify the interface connecting to the mininet network
        localIntf =  self.defaultIntf()
        
        if vlanid == 0 : 
            # assign the host's IP
            self.cmd( 'ifconfig %s inet %s' % ( localIntf, dhcpIp ) )
        else :
            # remove IP from default interface
            self.cmd( 'ifconfig %s inet 0' % localIntf )
            # create VLAN interface 
            self.cmd( 'vconfig add %s %d' % ( localIntf, vlanid ) )
            # assign the host's IP to the VLAN interface
            self.cmd( 'ifconfig %s.%d inet %s' % ( localIntf, vlanid,
                dhcpIp ) )
            # update the intf name and host's intf map
            newName = '%s.%d' % ( localIntf, vlanid )
            # update the (Mininet) interface to refer to VLAN interface name
            localIntf.name = newName
            # add VLAN interface to host's name to intf map
            self.nameToIntf[ newName ] = localIntf
        
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
        
        return dhcp
    
    def terminate( self ):
        """
        Stop DHCP Process and restore configuration
        """
        
        # Stop DHCP
        self.cmd( 'kill $(echo $(cat /var/run/dhcpd.pid))' )
        
        # Restore files
        self.cmd('cp /etc/dhcp/dhcpd.conf.bak /etc/dhcp/dhcpd.conf')
        self.cmd('cp /etc/default/isc-dhcp-server.bak /etc/default/isc-dhcp-server') 
         
        # Terminate
        super( Host, self ).terminate()

