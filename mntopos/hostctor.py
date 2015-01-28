#!/usr/bin/python

"""

This is a class constructor for Mininet hosts
- with static IP + default gateway
- with dhcp
- with or without VLAN

Pablo M. Guevara <pablomguevara@gmail.com>


"""

from mininet.cli import CLI
from mininet.log import lg
from mininet.log import setLogLevel, info, debug
from mininet.node import Node
from mininet.node import Host

class hostCtor( Host ):
    
    def config( self, gwIp='10.0.0.1', subnet='10.0/8', dhcp=False,
        vlanid=0, vlancos=0, **params ):
        
        """
        Configure host with default gateway 
        
        gwIP: the ip address of the gateway
        subnet: Mininet subnet (default 10.0/8)
        dhcp: False, use static IP
        vlanid: vlan support on hosts, 0 is no vlan
        
        TODO: add COS support
        """
        
        info('*** hostCtor VLAN %s\n' % vlanid)
         
        prefixLen = subnet.split( '/' )[ 1 ]
        
        host = super( Host, self ).config( **params )
                
        # Identify the interface connecting to the mininet network
        localIntf =  self.defaultIntf()
        
        if vlanid == 0 :
            
	    if dhcp == False :
                # assign the host's IP
                self.cmd( 'ifconfig %s inet %s' % ( localIntf, params['ip'] ) )
                # Add default gateway
                self.cmd( 'route add -net 0 gw %s' % gwIp )
            else :
                # remove IP from default, "physical" interface
                self.cmd( 'ifconfig %s inet 0' % localIntf )
                # initiate dhcp client
                self.cmd( 'dhclient %s &' % ( localIntf ) )
        
        else : # vlan is not 0, so configure vlan interface
            
            # remove IP from default, "physical" interface
            self.cmd( 'ifconfig %s inet 0' % localIntf )
            # create VLAN interface 
            self.cmd( 'vconfig add %s %d' % ( localIntf, vlanid ) )
            
            # Now, the IP assignment

            if dhcp == False :
                # assign the host's IP to the VLAN interface
                self.cmd( 'ifconfig %s.%d inet %s' % ( localIntf, vlanid,
                    params['ip'] ) )
                # Add default gateway
                self.cmd( 'route add -net 0 gw %s' % gwIp )
            else :
                # remove IP from default, "physical" interface
                self.cmd( 'ifconfig %s inet 0' % localIntf )
                # initiate dhcp client
                self.cmd( 'dhclient %s.%d &' % ( localIntf, vlanid ) )
            
            # update the intf name and host's intf map
            newName = '%s.%d' % ( localIntf, vlanid )
            # update the (Mininet) interface to refer to VLAN interface name
            localIntf.name = newName
            # add VLAN interface to host's name to intf map
            self.nameToIntf[ newName ] = localIntf
            
        return host

    def terminate ( self ):
        # Terminate dhcp clients just in case
        localIntf =  self.defaultIntf()
        self.cmd( 'pgrep -f "dhclient %s" > /dev/null && kill $(pgrep -f "dhclient %s" )'
            % ( localIntf, localIntf ) )
        
        # Terminate
        super( Host, self ).terminate()

