#!/usr/bin/env python
#-*- coding: utf-8 -*-

from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib.packet import icmp
from ryu.lib.packet import ipv4
from ryu.lib.packet import arp
from ryu.base import app_manager
from ryu.ofproto import ofproto_v1_3
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls


class SimpleRouter(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleRouter, self).__init__(*args, **kwargs)

        self.hw_addr_p1 = '70:88:99:00:00:01'
        self.ip_addr_p1 = '10.0.0.1'

        self.hw_addr_p2 = '70:88:99:00:00:02'
        self.ip_addr_p2 = '10.0.1.1'

    def _controller_actions(self, parser, ofproto):
        return [
            parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                   ofproto.OFPCML_NO_BUFFER)
        ]

    def _forward_actions(self, parser, ofproto, port, src, dst):

        return [
            parser.OFPActionSetField(eth_src=src),
            parser.OFPActionSetField(eth_dst=dst),
            parser.OFPActionDecNwTtl(),
            parser.OFPActionOutput(port)
        ]
 
    def _drop_actions(self, parser, ofproto):
        return []


    def _handle_icmp(self, datapath, port, pkt_ethernet, pkt_ipv4, pkt_icmp):

        if pkt_icmp.type != icmp.ICMP_ECHO_REQUEST:
            return

        pkt = packet.Packet()
        pkt.add_protocol(ethernet.ethernet(ethertype=pkt_ethernet.ethertype,
                                           dst=pkt_ethernet.src,
                                           src=pkt_ethernet.dst))
        pkt.add_protocol(ipv4.ipv4(dst=pkt_ipv4.src,
                                   src=pkt_ipv4.dst,
                                   proto=pkt_ipv4.proto,
                                   ttl=64))                      

        pkt.add_protocol(icmp.icmp(type_=icmp.ICMP_ECHO_REPLY,
                                   code=icmp.ICMP_ECHO_REPLY_CODE,
                                   csum=0,
                                   data=pkt_icmp.data))
        self._send_packet(datapath, port, pkt)

    def _handle_arp(self, datapath, port, pkt_ethernet, pkt_arp):
        if pkt_arp.opcode != arp.ARP_REQUEST:
            return
        pkt = packet.Packet()
        if pkt_ethernet.src == '00:00:00:00:00:01':
            pkt.add_protocol(ethernet.ethernet(ethertype=pkt_ethernet.ethertype,
                                               dst=pkt_ethernet.src,
                                               src=self.hw_addr_p1))
            pkt.add_protocol(arp.arp(opcode=arp.ARP_REPLY,
                                     src_mac=self.hw_addr_p1,
                                     src_ip=self.ip_addr_p1,
                                     dst_mac=pkt_arp.src_mac,
                                     dst_ip=pkt_arp.src_ip))
        else:
            pkt.add_protocol(ethernet.ethernet(ethertype=pkt_ethernet.ethertype,
                                               dst=pkt_ethernet.src,
                                               src=self.hw_addr_p2))
            pkt.add_protocol(arp.arp(opcode=arp.ARP_REPLY,
                                     src_mac=self.hw_addr_p2,
                                     src_ip=self.ip_addr_p2,
                                     dst_mac=pkt_arp.src_mac,
                                     dst_ip=pkt_arp.src_ip))

        self._send_packet(datapath, port, pkt)



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
    
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):

        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
  
        #LLDP Packets
        match_lldp = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_LLDP)
        actions_lldp = self._drop_actions(parser, ofproto)
        self.add_flow(datapath, 10000, match_lldp, actions_lldp)

        #IPv6 Packets
        match_ipv6 = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IPV6)
        actions_ipv6 = self._drop_actions(parser, ofproto)
        self.add_flow(datapath, 10000, match_ipv6, actions_ipv6)

        #Switch - Controller
        match_s1 = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP,
                                   ipv4_dst=('0.0.0.1', '0.0.0.255'))
        actions_s1 = self._controller_actions(parser, ofproto)
        self.add_flow(datapath, 1001, match_s1, actions_s1)

        #Host-1
        match_h1 = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP,
                                   ipv4_dst=('10.0.0.0', '255.255.255.0'))
        actions_h1 = self._forward_actions(parser, ofproto, 1,
                                           '77:88:99:00:00:01',
                                           '00:00:00:00:00:01')
        #priority=1                                  
        self.add_flow(datapath, 1000, match_h1, actions_h1)

        #Host-2
        match_h2 = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP,
                                   ipv4_dst=('10.0.1.0', '255.255.255.0'))
        actions_h2 = self._forward_actions(parser, ofproto, 2,
                                           '77:88:99:00:00:02',
                                           '00:00:00:00:00:02')
        #priority=1
        self.add_flow(datapath, 1000, match_h2, actions_h2)

        #Controller
        match = parser.OFPMatch()
        actions = self._controller_actions(parser, ofproto)
        self.add_flow(datapath, 0, match, actions)


    def add_flow(self, datapath, priority, match, actions, buffer_id=None, idle_timeout=0):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst,
                                    idle_timeout=idle_timeout)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst,
                                    idle_timeout=idle_timeout)
        datapath.send_msg(mod)

 
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
                                   
        #ICMP ECHO REQUEST
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(data=msg.data)
        pkt_ethernet = pkt.get_protocol(ethernet.ethernet)
        pkt_arp = pkt.get_protocol(arp.arp)

        if not pkt_ethernet:
            return

        pkt_ipv4 = pkt.get_protocol(ipv4.ipv4)
        pkt_icmp = pkt.get_protocol(icmp.icmp)

        if pkt_arp:
            self._handle_arp(datapath, in_port, pkt_ethernet, pkt_arp)
            return

        if pkt_icmp is not None:
            self._handle_icmp(datapath, in_port, pkt_ethernet, pkt_ipv4, pkt_icmp)
            return

   
