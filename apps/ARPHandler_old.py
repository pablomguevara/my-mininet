    def ARPHandler(self, datapath, pkt):
        # Handle only broadcast ARP Request
        # Unicast ARP is handled in data plane
        # ARPProxy for GW (possible extend in the future to other hosts)
        # From Upl, DROP ALL (we should not get these here)
        # From Dwl, If it's for GW => Proxy
        # From Dwl, If it's for other host => to Gw
        #
        # Broadcast ARP Reply is discarded
        
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
        pkt = packet.Packet(msg.data)
        pkt_eth = pkt.get_protocols(ethernet.ethernet)[0]
        pkt_arp = pkt.get_protocol(arp.arp)
        dst = pkt_eth.dst
        src = pkt_eth.src
        pkt_dhcp = pkt.get_protocol(dhcp.dhcp)
        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})
        
        # 1) ARP DST_IP = DHCP
        if pkt_arp.dst_ip == self.dhcp_ip:
            # if ARP Req is for DHCP, we Proxy
            _proxy_arp_response(datapath, dhcp_port, eth, pkt_arp,
                 self.dhcp_mac, self.dhcp_ip)
            # If it's dwl, learn
            if in_port != out_gw:
                # learn a mac address to avoid FLOOD next time.
                self.mac_to_port[dpid][src] = in_port
            
        # 2) ARP DST_IP = GW
        elif pkt_arp.dst_ip == self.gw_ip:
            # if ARP Req is for GW, we Proxy
            _proxy_arp_response(datapath, gw_port, eth, pkt_arp,
                 self.dhcp_mac, self.dhcp_ip)
            if in_port != out_gw:
                # learn a mac address to avoid FLOOD next time.
                self.mac_to_port[dpid][src] = in_port            
        
        # 3) in_port=upl
        elif in_port == out_gw:
            if dst == 'ff:ff:ff:ff:ff:ff' :
                # Uplink does not learn unicast
                # TODO other options? implement floodBcastArp? 
                out_port = ofproto.OFPP_FLOOD
            else:
                # Uplink does not learn unicast
                if dst in self.mac_to_port[dpid]:
                    # dst is known, we forward to dst
                    out_port = self.mac_to_port[dpid][dst]
                else:
                    # TODO: in the future we can implement floodUnknown
                    # for the time being we just discard unknown
                    out_port = 'DROP'  
            
        # 3) in_port= dwl (we should not get unicast ARP here)
        else:
            if dst != 'ff:ff:ff:ff:ff:ff':
                self.logger.debug("Got unicast ARP on downlink port, invalid")
                self.logger.debug("SRC MAC: %s ARP DST IP %s", src, pkt_arp.dst_ip)
            else
                # its a BCAST ARP on a dwl, we already forwarded to GW
                # learn mac address to avoid FLOOD next time, and drop
                self.mac_to_port[dpid][src] = in_port
                
 
