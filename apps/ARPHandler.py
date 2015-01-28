    def ARPHandler(self, datapath, in_port, pkt):
        # Description:
        # ARP Request DHCP, Proxy
        # ARP Request GW, Proxy
        # ARP Request other than GW/DHCP on dwl, to GW
        # ARP Request on upl
        #     Bcast flood
        #     Unknown ucast flood
        #     known ucast forward to dst
        # Returns out_port for flow_mod or packet_out
        
        ofproto = datapath.ofproto
        pkt = packet.Packet(msg.data)
        pkt_eth = pkt.get_protocols(ethernet.ethernet)[0]
        pkt_arp = pkt.get_protocol(arp.arp)
        dst = pkt_eth.dst
        src = pkt_eth.src
        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})
        out_gw = self.port_map[dpid]['gw']
        out_dhcp = self.port_map[dpid]['dhcp']
        
        # TODO        
        # Handle incoming DHCP Requests Rx on dwl, learn and discard
        # Handle incoming BCAST ARP Requests Rx on dwl, learn and discard
        if pkt_arp :
            if pkt_arp.dst_mac == self.gw_mac:
                self._proxy_arp_response(datapath, out_port, pkt_eth, pkt_arp,
                                         self.gw_mac, self.gw_ip)
                return 'DROP'
            elif pkt_arp.dst_mac == self.dhcp_mac:
                self._proxy_arp_response(datapath, out_port, pkt_eth, pkt_arp,
                                         self.dhcp_mac, self.dhcp_ip)
                return 'DROP'
            elif ( in_port != out_gw ) and ( in_port != out_dhcp ) :
                return gw_port
            elif ( in_port == out_gw ) or ( in_port == out_dhcp ) :
                if dst == 'ff:ff:ff:ff:ff:ff':
                    #TODO Avoid flooding DHCP port, send only to dwl
                    return .ofproto.OFPP_FLOOD
                else:
                    if dst in self.mac_to_port[dpid]:
                        return out_port = self.mac_to_port[dpid][dst]
                    else:
                        return out_port = ofproto.OFPP_FLOOD
            else:
                # Unhandled case, log and do nothing
                self.logger.debug('Unhandled ARP %s', pkt_arp)
                self.logger.debug('DPID %s SRC MAC %s DST MAC %s',
                    dpid, src, dst)
                return 'DROP'
            
            
            
            
            
