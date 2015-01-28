from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller import dpset
from ryu.controller.handler import CONFIG_DISPATCHER
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.topology import api
from ryu.lib.packet import arp
from ryu.topology import switches
from ryu.lib.packet import dhcp

"""
HSIA Service Application
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Downstream 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Version 1 - drops mcast and bcast, except dhcp and arp
- Install flows on even packet_in
- Unicast, first version drops unknown
- ARP => fwToARPHandler
- DHCP => fwToDHCPHandler
- Multicast => DROP
- Broadcast => DROP

Priority    Flow description
100         forward to user based on dst mac
102         dhcp handler (match port_in, udp src/dst)
102         arp handler (match port_in, udp src, sdt)
101         default rule for bcast (match port_in, dst ff:ff:ff:ff:ff:ff)
101         default rule for mcast

Upstream ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Version 1 - send all to GW or DHCP Server 
- Install flows on discovery phase
- Default flow is match(in_port) action(gw_port)
- Exceptions => ARP, DHCP, LLDP (LLDP handled by ryu with --observe-links)
- Exception flows need to have more priority than the data flow so we can process
these exceptions

Priority    Flow description
100         default rule to gateway
102         dafault rule to dhcp (match port_in, udp src/dst)
102         default rule to arp handler (match port_in, udp src, sdt)
101         default rule for bcast (match port_in, dst ff:ff:ff:ff:ff:ff)
101         default rule for mcast

Skeleton is based on simple_switch_13.py from ryu-book

Pablo M. Guevara <pablomguevara@gmail.com>


"""

class HsiaService13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    
    _CONTEXTS = { 'switches': switches.Switches,
                  'dpset': dpset.DPSet }
    
    def __init__(self, *args, **kwargs):
        super(HsiaService13, self).__init__(*args, **kwargs)
        
        # MAC Address to port mapping
        self.mac_to_port = {}
        
        # Datapath structure
        self.datapaths = {}
        
        # Start with manual assignment
        # Structure that stores data path id and the port map for gw and dhcp
        # ports
        
        # gw_port = [{'dpid' : 1, 'gw' : 1, 'dhcp' : 2},
        #           {'dpid' : 2, 'gw' : 1, 'dhcp' : 1},
        #           {'dpid' : 3, 'gw' : 1, 'dhcp' : 1},
        #           {'dpid' : 4, 'gw' : 1, 'dhcp' : 1}]

        self.port_map = { 1 : { 'gw' : 1, 'dhcp' : 2 },
                          2 : { 'gw' : 1, 'dhcp' : 1 },
                          3 : { 'gw' : 1, 'dhcp' : 1 },
                          4 : { 'gw' : 1, 'dhcp' : 1 }
                        }
        
        # To append use:
        # self.gw_port.append({'dpid' : 5, 'gw' : 1, 'dhcp' : 1})
        
        self.dhcp_ip = "10.0.0.254"
        self.gw_ip = "10.0.0.1"
        self.gw_mac = "00:00:00:bb:bb:bb"
        self.dhcp_mac = "00:00:00:aa:aa:aa"
        self.switches = kwargs['switches'] 

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install table-miss flow entry
        #
        # We specify NO BUFFER to max_len of the output action due to
        # OVS bug. At this moment, if we specify a lesser number, e.g.,
        # 128, OVS will send Packet-In with invalid buffer_id and
        # truncated packet data. In that case, we cannot output packets
        # correctly.
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)
        
        # First version static flow definition
        print "Switch Connection"
        print "Data Path ID %d" % datapath.id
        
        # Attempt to print links
        print [link.to_dict() for link in api.get_all_link(self).iterkeys()]
        
        # Print linst for c1
        #print "Print links for c1"
        #c1_links = api.get_link(self,dpid=1)
        #for link in c1_links:
        #    print link
        
        # Code to test switches.py
        print "----- We print here to learn how it works, using switches.py ---"
        for sw in self.switches.dps:
            print self.switches.dps[sw].ports
        print "----- END Printing switches ------------------------------------"
    
    @set_ev_cls(ofp_event.EventOFPStateChange,
        [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
    # Add or remove datapath
        self._packet_in_handler
        datapath = ev.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        dpid = datapath.id
        if ev.state == MAIN_DISPATCHER:
            if not dpid in self.datapaths:
                self.logger.debug('register datapath: %016x', dpid)
                self.datapaths[dpid] = datapath
                # Add static flows for Gateway/DHCP Ports
                # iterate on ports...
                self.logger.debug('adding static flows on datapath %016x', dpid)
                for port in self.switches.dps[dpid].ports.iterkeys():        
                    # Add flows for in_port on all ports except gw/dhcp
                    # TODO investigate why there is a port with the name of the
                    # switch and hight port numbering example: 4294967294
                    out_gw = self.port_map[dpid]['gw']
                    out_dhcp = self.port_map[dpid]['dhcp']
                    
                    # PACKET COMES IN ON DOWNLINK PORTS (Upstream direction)
                    if port <= 1000 and port != out_gw and port != out_dhcp :
                        # GATEWAY FLOW
                        # inbound pkt on dwl send to gw
		        self.to_gw(out_gw, port, datapath)
                        # DHCP FLOW
                        # inbound dhcp on dwl send to ctrl and dhcp
                        self.to_dhcp(out_dhcp, port, datapath)
                        # BCAST ARP FLOW
                        # inbound bcast arp on dwl send to ctrl and gw
                        self.to_arp(out_gw, port, datapath)
                        
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.debug('unregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]
    
    def to_gw(self, out_port, in_port, datapath):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        dpid = datapath.id
        # GATEWAY FLOW
        self.logger.debug('add permanent GW flow dpid %016x in_port %i out_port %i',
            dpid, in_port, out_port)
        gwMatch = parser.OFPMatch( in_port=in_port )
        gwActions = [parser.OFPActionOutput(out_port)]
        self.add_flow(datapath, 100, gwMatch, gwActions, idle_timeout=0,
            hard_timeout=0)
        self.logger.debug("inst def flow in %s %i", dpid, in_port)

    def to_dhcp(self, out_port, in_port, datapath):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        dpid = datapath.id
        # DHCP FLOW
        # send to DHCP and CONTROLLER for learning
        self.logger.debug('add permanent DHCP flow dpid %016x in_port %i out_port %i',
            dpid, in_port, out_port)
        dhcpMatch = parser.OFPMatch(in_port=in_port, eth_type=0x800, ip_proto=17,
            udp_src=68, udp_dst=67 )
        dhcpActions = [parser.OFPActionOutput(out_port),
            parser.OFPActionOutput(ofproto.OFPP_CONTROLLER)]
        self.add_flow(datapath, 102, dhcpMatch, dhcpActions, idle_timeout=0,
            hard_timeout=0)
        self.logger.debug("inst dhcp flow in %s %i", dpid, in_port)

    def to_arp(self, out_port, in_port, datapath):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        dpid = datapath.id
        # BCAST ARP FLOW
        # send to GW and CONTROLLER for learning
        self.logger.debug('add permanent BCAST ARP dpid %016x in_port %i out_port %i',
            dpid, in_port, out_port)
        arpMatch = parser.OFPMatch(in_port=in_port, eth_type=0x0806,
            eth_dst='ff:ff:ff:ff:ff:ff')
        arpActions = [parser.OFPActionOutput(out_port),
            parser.OFPActionOutput(ofproto.OFPP_CONTROLLER)]
        self.add_flow(datapath, 102, arpMatch, arpActions, idle_timeout=0,
            hard_timeout=0)
        self.logger.debug("inst dhcp flow in %s %i", dpid, in_port)

    @set_ev_cls(ofp_event.EventOFPPortStatus, CONFIG_DISPATCHER)
    def port_status_handler (self, ev):
        msg = ev.msg
    
        reason = msg.reason
        port_no = msg.desc.port_no
        print('HSIA Service - port_status_handler {}'.format(msg.desc))
        ofproto = msg.datapath.ofproto
        if reason == ofproto.OFPPR_ADD:
            self.logger.info("port added %s", port_no)
            pass
        elif reason == ofproto.OFPPR_DELETE:
            self.logger.info("port deleted %s", port_no)
            pass
        elif reason == ofproto.OFPPR_MODIFY:
            self.logger.info("port modified %s", port_no)
            pass
        else:
            self.logger.info("Illeagal port state %s %s", port_no, reason)
            pass
    
    def add_flow(self, datapath, priority, match, actions, idle_timeout=0,
        hard_timeout=0, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match, 
                                    instructions=inst,
                                    idle_timeout=idle_timeout,
                                    hard_timeout=hard_timeout)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst,
                                    idle_timeout=idle_timeout,
                                    hard_timeout=hard_timeout)
        datapath.send_msg(mod)

    def DHCPHandler(self, datapath, in_port, pkt):
        # op	Message op code / message type. 1 = BOOTREQUEST, 2 = BOOTREPLY
        # DHCP Request - 1
        # From Upl, DROP ALL
        # From Dwl, Send to DHCP
        #
        # DHCP Reply - 2
        # From Dwl, DROP ALL 
        # From DHCP Port or GW, Forward if known/Flood otherwise

        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
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
        
        self.logger.debug('DHCPHandler: dpid %s out port %s',
            dpid, out_port)
        self.logger.debug("packet-out %s" % (pkt,))
        
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)
    
    def ARPHandler(self, datapath, in_port, pkt):
        # Dwl inbound UCAST ARP is sent to GW
        # Dwl inbound BCAST ARP is sent to GW and copy to CTRL
        # Upl inbound UCAST ARP send to PORT or DROP
        # Upl inbound BCAST ARP FLOOD
        # * inbound for DHCP/GW ProxyARP and Learn
         
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        pkt_eth = pkt.get_protocols(ethernet.ethernet)[0]
        pkt_arp = pkt.get_protocol(arp.arp)
        dst = pkt_eth.dst
        src = pkt_eth.src
        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        out_gw = self.port_map[dpid]['gw']
        out_dhcp = self.port_map[dpid]['dhcp']
        
        # 1) ARP DST_IP = DHCP
        if pkt_arp.dst_ip == self.dhcp_ip:
            # if ARP Req is for DHCP, we Proxy
            self._proxy_arp_request(datapath, in_port, pkt_eth, pkt_arp,
                 self.dhcp_mac, self.dhcp_ip)
            # If it's dwl, learn
            if in_port != out_gw:
                # learn a mac address to avoid FLOOD next time.
                self.mac_to_port[dpid][src] = in_port
            # No further processing needed
            return
            
        # 2) ARP DST_IP = GW
        elif pkt_arp.dst_ip == self.gw_ip:
            # if ARP Req is for GW, we Proxy
            self._proxy_arp_request(datapath, in_port, pkt_eth, pkt_arp,
                 self.gw_mac, self.gw_ip)
            # If it's dwl, learn
            if in_port != out_gw:
                # learn a mac address to avoid FLOOD next time.
                self.mac_to_port[dpid][src] = in_port
            # No further processing needed
            return
        
        # 3) in_port=upl or in_port=dhcp
        elif in_port == out_gw or in_port == out_dhcp:
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
                    self.logger.debug('Discarding unknown unicast on upl')
                    self.logger.debug('SRC MAC = %s DPID = %s', src, dpid)
                    # UCATS ARP with unknown dest, DROP
                    return
        
        # 3) in_port= dwl (we should not get unicast ARP here)
        else:
            if dst != 'ff:ff:ff:ff:ff:ff':
                self.logger.debug("Got unicast ARP on downlink port, invalid")
                self.logger.debug("SRC MAC: %s ARP DST IP %s", src, pkt_arp.dst_ip)
                # This is an error condition
                return
            else:
                # its a BCAST ARP on a dwl, we already forwarded to GW
                # learn mac address to avoid FLOOD next time, and drop
                self.mac_to_port[dpid][src] = in_port
                return
        
        # If we are still here we have flows to install
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
        
        self.logger.debug('ARPHandler: dpid %s out port %s',
            dpid, out_port)
        self.logger.debug("packet-out %s" % (pkt,))
        
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)

    def _proxy_arp_request(self, datapath, out_port, pkt_eth, pkt_arp, _src_mac, _src_ip):
        if pkt_arp.opcode != arp.ARP_REQUEST:
            return
        pkt = packet.Packet()
        pkt.add_protocol(ethernet.ethernet(ethertype=pkt_eth.ethertype,
            dst=pkt_eth.src,
            src=_src_mac))
        pkt.add_protocol(arp.arp(opcode=arp.ARP_REPLY,
            src_mac=_src_mac,
            src_ip=_src_ip,
            dst_mac=pkt_arp.src_mac,
            dst_ip=pkt_arp.src_ip))
        self._send_packet(datapath, out_port, pkt)

    def _send_packet(self, datapath, out_port, pkt):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        pkt.serialize()
        self.logger.debug('_send_packet: dpid %s out port %s',
            datapath.id, out_port)      
        self.logger.debug("packet-out %s" % (pkt,))
        data = pkt.data
        actions = [parser.OFPActionOutput(port=out_port)]
        out = parser.OFPPacketOut(datapath=datapath,
            buffer_id=ofproto.OFP_NO_BUFFER,
            in_port=ofproto.OFPP_CONTROLLER,
            actions=actions,
            data=data)
        datapath.send_msg(out)
    
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
        pkt = packet.Packet(msg.data)
        pkt_eth = pkt.get_protocols(ethernet.ethernet)[0]
        pkt_arp = pkt.get_protocol(arp.arp)
        pkt_dhcp = pkt.get_protocol(dhcp.dhcp)
        dst = pkt_eth.dst
        src = pkt_eth.src
        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})
        self.logger.debug("packet in %s %s %s %s ethType %s", dpid, src, dst,
            in_port, pkt_eth.ethertype)
        
        if not pkt_eth:
            # Not an ethernet frame
            return
        elif pkt_arp:
            # If its bcast ARP, handle it
            self.ARPHandler(datapath, in_port, pkt)
            return
        elif pkt_dhcp:
            # If its DHCP, handle it
            self.DHCPHandler(datapath, in_port, pkt) 
            return
        
        # If we are here it's not ARP or DHCP
         
        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port
         
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

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
        
        self.logger.debug('simple_switch: dpid %s out port %s',
            dpid, out_port)
        self.logger.debug("packet-out %s" % (pkt,))

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)

