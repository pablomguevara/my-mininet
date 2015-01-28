from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import arp
from ryu.lib.packet import dhcp


"""
HSIA Simple Service Application
- 1 Gateway port, 1 DHCP port
- FLOOD Bcast on downstream
- Forward to Gateway or DHCP on upstream
- Port 1 is considered to be the gateway all should be able to comunicate 
  with h1
- No host to host communication

Downstream ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Bcast flood
Mcast TODO
Ucast known Install flows on event packet_in
Ucast unknown flood downlinks

Upstream ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
ARP, DHCP, Send to controller for learning and to gateway, then DROP
Install default flows on discovery phase
Default flow is match(in_port) action(gw_port)

Skeleton is based on simple_switch_13.py from ryu-book

Pablo M. Guevara <pablomguevara@gmail.com>


"""

class SimpleHsiaService13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
        
    def __init__(self, *args, **kwargs):
        super(SimpleHsiaService13, self).__init__(*args, **kwargs)
        
        # MAC Address to port mapping
        self.mac_to_port = {}
        
        # Datapath structure
        self.datapaths = {}
        
        # Upl/Dwl assignment
        self.port_map = { 1 : { 'gw' : 1, 'dhcp' : 2 } }
        
        # GW IP and MAC
        self.gw_mac = '00:00:00:aa:aa:aa'
        self.gw_ip = '10.0.0.1'
        self.dhcp_mac = '00:00:00:bb:bb:bb'
        self.dhcp_ip = '10.0.0.254'        
        
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
        
        self.logger.debug('Switch connection DPID %016x', datapath.id)
    
    @set_ev_cls(ofp_event.EventOFPStateChange,
        [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
    # Add or remove datapath
        self._packet_in_handler
        datapath = ev.datapath
        dpid = datapath.id
        if ev.state == MAIN_DISPATCHER:
            if not dpid in self.datapaths:
                self.logger.debug('register datapath: %016x', dpid)
                self.datapaths[dpid] = datapath
                self.add_static_flows(datapath)            
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.debug('unregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]
    
    def add_static_flows(self, datapath)
        # Add static flows for Gateway/DHCP Ports
        # iterate on ports...
        dpid = datapath.id
        ports = get_ports(dpid)
        self.logger.debug('adding static flows on datapath %016x', dpid)
        out_gw = self.port_map[dpid]['gw']
        out_dhcp = self.port_map[dpid]['dhcp'] 
        for port in ports:        
            # Add flows for in_port on all ports except gw=1
            # Packet comes in on upl or dhcp port we handle it on packet_in
            if (port =! self.port_map[dpid]['gw']) and
               (port =! self.port_map[dpid]['dhcp']):
                # GATEWAY FLOW
                # Se send to GW all packets in on dwl
                self.gw_static_flow(datapath, port, out_gw)
                # DHCP FLOW
                # We send to DHCP all DHCP Requests on dwl, send copy to CTRL
                self.dhcp_static_flow(datapath, port, out_dhcp)
                # ARP FLOW
                # We send to GW/DHCP all BCAST ARP Requests on dwl, send copy to CTRL
                self.arp_static_flow(datapath, port, out_gw)
                self.arp_static_flow(datapath, port, out_dhcp)
    
    def arp_static_flow(self, datapath, in_port, out_port)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        match = parser.OFPMatch( in_port=in_port, 
                                 eth_dst='ff:ff:ff:ff:ff:ff', 
                                 eth_type='0x0806'
                                 arp_op=arp.ARP_REQUEST )
        actions = [parser.OFPActionOutput( out_port, ofproto.OFPP_CONTROLLER )]
        self.add_flow(self, datapath, 101, match, actions, idle_timeout=0,
        hard_timeout=0)
    
    def dhcp_static_flow(self, datapath, in_port, out_port)
        # Since we match udp src 68, we match only DHCP Request
        # op is redundant and not needed on this match
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        match = parser.OFPMatch( in_port=port,
                                 udp_src=68, udp_dst=67,
                                 ip_proto=17 )
        actions = [parser.OFPActionOutput( out_port, ofproto.OFPP_CONTROLLER )]
        self.add_flow(self, datapath, 102, match, actions, idle_timeout=0,
        hard_timeout=0)
        
    def gw_static_flow(self, datapath, in_port, out_port)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        match = parser.OFPMatch( in_port=port )
        actions = [parser.OFPActionOutput( out_port )]
        self.add_flow(self, datapath, 103, match, actions, idle_timeout=0,
        hard_timeout=0)
             
    def add_flow(self, datapath, priority, match, actions, idle_timeout=None,
        hard_timeout=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)
        if idle_timeout != None:
            if hard_timeout != None:
                mod = parser.OFPFlowMod(datapath=datapath,
                                        priority=priority,
                                        match=match, instructions=inst,
                                        idle_timeout=idle_timeout,
                                        hard_timeout=hard_timeout)
            else:
                mod = parser.OFPFlowMod(datapath=datapath,
                                        priority=priority,
                                        match=match, instructions=inst,
                                        idle_timeout=idle_timeout)
        else:
            mod = parser.OFPFlowMod(datapath=datapath,
                                    priority=priority,
                                    match=match, instructions=inst,)
        datapath.send_msg(mod)
    
    def _proxy_arp_response(self, datapath, out_port, pkt_ethernet, pkt_arp,
        _src_mac, _src_ip):
        if pkt_arp.opcode != arp.ARP_REQUEST:
            return
        pkt = packet.Packet()
        pkt.add_protocol(ethernet.ethernet(ethertype=pkt_ethernet.ethertype,
        dst=pkt_ethernet.src,
        src=self.hw_addr))
        pkt.add_protocol(arp.arp(opcode=arp.ARP_REPLY,
                                 src_mac=_src_mac,
                                 src_ip=_src_ip,
                                 dst_mac=pkt_arp.src_mac,
                                 dst_ip=pkt_arp.src_ip))
        self._send_packet(datapath, out_port, pkt)

    def _send_packet(self, datapath, port, pkt):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        pkt.serialize()
        self.logger.info("packet-out %s" % (pkt,))
        data = pkt.data
        actions = [parser.OFPActionOutput(port=port)]
        out = parser.OFPPacketOut(datapath=datapath,
                                  buffer_id=ofproto.OFP_NO_BUFFER,
                                  in_port=ofproto.OFPP_CONTROLLER,
                                  actions=actions,
                                  data=data)
        datapath.send_msg(out)

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

    def DHCPHandler(self, datapath, in_port, pkt):
        # op	Message op code / message type. 1 = BOOTREQUEST, 2 = BOOTREPLY
        # DHCP Request - 1
        # From Upl, DROP ALL
        # From Dwl, Send to DHCP
        #
        # DHCP Reply - 2
        # From Dwl, DROP ALL 
        # From DHCP Port or GW, Forward if known/Flood otherwise

        datapath = msg.datapath
        ofproto = datapath.ofproto
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

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
        pkt = packet.Packet(msg.data)
        pkt_eth = pkt.get_protocols(ethernet.ethernet)[0]
        dst = pkt_eth.dst
        src = pkt_eth.src
        pkt_arp = pkt.get_protocol(arp.arp)
        pkt_dhcp = pkt.get_protocol(dhcp.dhcp)
        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})
        out_gw = self.port_map[dpid]['gw']
        out_dhcp = self.port_map[dpid]['dhcp']

        self.logger.debug("packet in %s %s %s %s", dpid, src, dst, in_port)
        
        # Handle ARP Requests
        if pkt_arp and pkt_arp = arp.ARP_REQUEST:
            out_port = ARPHandler(datapath, in_port, pkt)
        # Handle DHCP
        if pkt_dhcp:
            out_port = DHCPHandler(datapath, in_port, pkt)
        else:
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
            self.add_flow(datapath, 1, match, actions)

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)
