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
    
    def config( self, gwIp='10.255.255.254', subnet='10.0/8', dhcp=False,
        vlanid=0, vlancos=0, **params ):
        
        """
        Configure host with default gateway 
        gwIP: the ip address of the gateway
        subnet: Mininet subnet (default 10.0/8)
        dhcp: False, use static IP
        vlanid: vlan support on hosts, 0 is no vlan
        
        TODO: add COS support
        """
        debug('*** hostCtor ip ', params['ip'])
        info('*** hostCtor VLAN %s\n' % vlanid)
        
        # We play a little game here, we don't want super config
        # to put the ip on the host if we are setting up DHCP or VLAN
        # so, if this is DHCP or VLAN we set IP to None, and we store
        # the value to use it later. This is because ONOS does not like
        # ONOS populates both addresses 2 times and it looks like there
        # are 2 different hosts.

        if dhcp == True or vlanid != 0 :
            aux_ip = params['ip']
            params['ip'] = None
 
        prefixLen = subnet.split( '/' )[ 1 ]
        
        host = super( Host, self ).config( **params )
        
        # Now we copy the original value of the IP address
        if dhcp == True or vlanid != 0 :
            params['ip'] = aux_ip

        # Identify the interface connecting to the mininet network
        localIntf =  self.defaultIntf()
        debug('*** Host default interface ', localIntf, '\n')
        debug('*** Host interfaces ', self.nameToIntf, '\n')

        if vlanid == 0 :
            
	    if dhcp == False :
                # assign the host's IP
                self.cmd( 'ifconfig %s inet %s' % ( localIntf, params['ip'] ) )
                # Add default gateway
                self.cmd( 'route add -net 0 gw %s' % gwIp )
            else :
                # initiate dhcp client
                self.cmd( 'dhclient %s &' % ( localIntf ) )
        
        else : # vlan is not 0, so configure vlan interface
            
            # remove IP from default, "physical" interface
            self.cmd( 'ifconfig %s inet 0' % localIntf )
            # create VLAN interface 
            self.cmd( 'vconfig add %s %d' % ( localIntf, vlanid ) )
            debug('*** Host default interface ', localIntf, '\n')
            debug('*** Host interfaces ', self.nameToIntf, '\n')
            # Now, the IP assignment

            if dhcp == False :
                # assign the host's IP to the VLAN interface
                self.cmd( 'ifconfig %s.%d inet %s' % ( localIntf, vlanid,
                    params['ip'] ) )
                # Add default gateway
                self.cmd( 'route add -net 0 gw %s' % gwIp )
                debug('*** Host default interface ', localIntf, '\n')
                debug('*** Host interfaces ', self.nameToIntf, '\n')
            else :
                # initiate dhcp client
                self.cmd( 'dhclient %s.%d &' % ( localIntf, vlanid ) )
            
            # update the intf name and host's intf map
            newName = '%s.%d' % ( localIntf, vlanid )
            
            # update the (Mininet) interface to refer to VLAN interface name
            localIntf.name = newName
            debug('*** Host default interface ', localIntf, '\n')
            debug('*** Host interfaces ', self.nameToIntf, '\n')
       
            # add VLAN interface to host's name to intf map
            self.nameToIntf[ newName ] = localIntf
            debug('*** Host default interface ', localIntf, '\n')
            debug('*** Host interfaces ', self.nameToIntf, '\n')
            
            # neet to re-apply the IP, if not mininet thinks it's None
            self.setIP(params['ip'], intf=localIntf)
            
            # TODO
            # There seems to be a problem with the interface manipulation
            # avobe. This is an example interface config:
            # *** Host interfaces  {'h1-eth0.10': <TCIntf h1-eth0.10>, 
            # 'h1-eth0': <TCIntf h1-eth0.10>} 
            # I would expect h1-eth0 to be <TCIntf he-eth0>, but it's not. I 
            # don't know why and I don't know how to fix it, but since the 
            # primary interface used by mininet is ok, it works.
            #

        return host

    def terminate ( self ):
        # Terminate dhcp clients just in case
        localIntf =  self.defaultIntf()
        self.cmd( 'pgrep -f "dhclient %s" > /dev/null && kill $(pgrep -f "dhclient %s" )'
            % ( localIntf, localIntf ) )
        
        # Terminate
        super( Host, self ).terminate()

