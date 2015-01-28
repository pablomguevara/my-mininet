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
            if in_port != gw_port and n_port != dhcp_port:
                # We already forwarded to DHCP, learn and DROP
                self.mac_to_port[dpid][src] = in_port
                return
            else:
                # Got a request on an upl/dhcp port, DROP
                self.logger.debug('Ilegal DHCP Request on SW %s port %s',
                    in_port, dpid)
                return
        elif pkt_dhcp.op == '2':
            if in_port != out_dhcp:
                # Got a reply on a non DHCP port, DROP
                self.logger.debug('Ilegal DHCP Reply on non DHCP SW %s port %s',
                    in_port, dpid)
                return
            else:
                if dst == 'ff:ff:ff:ff:ff:ff':
                    # Flood
                    out_port = ofproto.OFPP_FLOOD
                else:
                    # Forward
                    if dst in self.mac_to_port[dpid]:
                        out_port = self.mac_to_port[dpid][dst]
                    else:
                        out_port = ofproto.OFPP_FLOOD
        
        # If we are here we need to flood/forward
        
                actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
            # verify if we have a valid buffer_id, if yes avoid to send both
            # flow_mod & packet_out
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                return
            else:
                self.add_flow(datapath, 1, match, actions)
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)
        
                
                
