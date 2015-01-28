#!/usr/bin/python
# Script that parses ovs output.
# Example flow OF1.3
# skb_priority(0),in_port(4),eth(src=00:00:01:00:00:02/00:00:00:00:00:00,dst=c6:95:63:d4:f7:45/ff:ff:ff:ff:ff:ff),eth_type(0x8100),encap(eth_type(0x0800),ipv4(src=10.0.0.3,dst=192.168.143.254,proto=1,tos=0,ttl=64,frag=no),icmp(type=8,code=0)), packets:702, bytes:70504, used:0.084s, actions:3

# OLD FLOWS, maybe OF 1 or 1.1 ? Check!!!!
# in_port(2),eth(src=00:26:55:e8:b0:43,dst=bc:30:5b:f7:07:fc),eth_type(0x0806),arp(sip=193.170.192.129,tip=193.170.192.142,op=2,sha=00:26:55:e8:b0:43,tha=bc:30:5b:f7:07:fc), packets:0, bytes:0, used:never, actions:1
#in_port(2),eth(src=bc:30:5b:f6:dd:fc,dst=bc:30:5b:f7:07:fc),eth_type(0x0800),ipv4(src=193.170.192.143,dst=193.170.192.142,proto=6,tos=0,ttl=64,frag=no),tcp(src=45969,dst=5672), packets:1, bytes:87, used:4.040s, flags:P., actions:1
# in_port(2),eth(src=bc:30:5b:f6:dd:fc,dst=bc:30:5b:f7:07:fc),eth_type(0x0800),ipv4(src=193.170.192.143,dst=193.170.192.142,proto=6,tos=0,ttl=64,frag=no),tcp(src=45992,dst=5672), packets:118412, bytes:21787661, used:2.168s, flags:P., actions:1

from pyparsing import *
import datetime,time
import os
f = os.popen('ovs-dpctl dump-flows ovs-system')
flows = f.readlines()
print "~~~~~~~~~~~~~~~~~~~~~~ Flows ~~~~~~~~~~~~~~~~~~~~~~~"
for f in flows :
    print "%s" % f
    print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"

LBRACE,RBRACE,COMMA,EQUAL,COLON,FWDBAR = map(Suppress,'(),=:/')
in_port = skb_priority = packets = proto = tos = ttl = Word(nums) 
src = dst = s_mask = d_mask = op = _type = code = Word(nums)
ipAddress = Combine(Word(nums) + ('.' + Word(nums))*3)
twohex = Word(hexnums,exact=2)
macAddress = macMask = Combine(twohex + (':'+twohex)*5)
vlan_eth_type = eth_type = Combine('0x' + Word(hexnums,exact=4))
frag = Word

frag = oneOf("yes no")

eth = Group("eth" + LBRACE + 
                "src" + EQUAL + macAddress("src") + FWDBAR + macMask("s_mask") +
                COMMA +
                "dst" + EQUAL + macAddress("dst") + FWDBAR + macMask("d_mask") +
                RBRACE)
arp = Group("arp" + LBRACE +
                "sip" + EQUAL + ipAddress("sip") + COMMA +
                "tip" + EQUAL + ipAddress("tip") + COMMA +
                "op" + EQUAL + op("op") + COMMA + 
                "sha" + EQUAL + macAddress("sha") + COMMA + 
                "tha" + EQUAL + macAddress("tha") + 
                RBRACE)
ipv4 = Group("ipv4" + LBRACE + "src" + EQUAL + ipAddress("src") + COMMA + 
                "dst" + EQUAL + ipAddress("dst") + COMMA + 
                "proto" + EQUAL + proto("proto") + COMMA + 
                "tos" + EQUAL + tos("tos") + COMMA + 
                "ttl" + EQUAL + ttl("ttl") + COMMA + 
                "frag" + EQUAL + frag("frag") + 
                RBRACE)
tcp = Group("tcp" + LBRACE + 
                "src" + EQUAL + src("srcPkt") + COMMA + 
                "dst" + EQUAL + dst("dstPkt") + 
                RBRACE)

# icmp(type=8,code=0)
icmp = Group( "icmp" + LBRACE + "type" + EQUAL + _type("type") + COMMA +
                "code" + EQUAL + code("code") + RBRACE )

flowTcp = ( "skb_priority" + LBRACE + skb_priority("skb_priority") + RBRACE + COMMA +
            "in_port" + LBRACE + in_port("in_port") + RBRACE + COMMA + 
            eth("eth") + COMMA + 
            Optional("eth_type" + LBRACE + eth_type("eth_type") + RBRACE + COMMA ) +
            Optional(arp("arp") + COMMA) +
            Optional(ipv4("ipv4") + COMMA) +
            Optional(tcp("tcp") + COMMA) +
            Optional(icmp("icmp") + COMMA) +
            Optional("encap" + LBRACE +
                Optional(Optional(eth_type("eth_type") + COMMA ) +
                Optional(ipv4("ipv4") + COMMA) +
                Optional("eth_type" + LBRACE + vlan_eth_type("eth_type") + RBRACE 
            "packets" + COLON + packets("packets"))

for f in flows:
    flowTcpValues = flowTcp.parseString(f)
    print flowTcpValues.dump()
    print flowTcpValues.packets
    print flowTcpValues.eth.src
    print flowTcpValues.eth.dst
    print

