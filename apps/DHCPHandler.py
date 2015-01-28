    def DHCPHandler(self, datapath, pkt):
        # op	Message op code / message type. 1 = BOOTREQUEST, 2 = BOOTREPLY
        # DHCP Request - 1
        # From Upl, DROP ALL
        # From Dwl, Send to DHCP
        #
        # DHCP Reply - 2
        # From Dwl, DROP ALL 
        # From DHCP Port or GW, Forward if known/Flood otherwise

        msg = ev.msg
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
        
        out_gw = self.port_map[dpid]['gw']
        out_dhcp = self.port_map[dpid]['dhcp']
        
        if pkt_dhcp.op == '1':
            # BOOT REQUEST
            if in_port != gw_port and in_port != dhcp_port:
                # We already forwarded to DHCP, learn and DROP
                self.mac_to_port[dpid][src] = in_port
                return 'DROP'
            else:
                # Got a request on an upl/dhcp port, DROP
                self.logger.debug('Ilegal DHCP Request on SW %s port %s',
                    in_port, dpid)
                return 'DROP'
        else:
            # BOOT REPLY
            if in_port != out_dhcp and in_port != out_gw :
                # Got a reply on a non DHCP port, DROP
                self.logger.debug('Ilegal DHCP Reply on non DHCP SW %s port %s',
                    in_port, dpid)
                return 'DROP'
            else:
                if dst == 'ff:ff:ff:ff:ff:ff':
                    # TODO Avoid flooding GW port
                    return out_port = ofproto.OFPP_FLOOD
                else:
                    # Forward if known, flood otherwise
                    if dst in self.mac_to_port[dpid]:
                        return out_port = self.mac_to_port[dpid][dst]
                    else:
                        return out_port = ofproto.OFPP_FLOOD
