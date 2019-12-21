#!/usr/bin/env python3

"""Shortest Path Switching template
CSCI1680
This example creates a simple controller application that watches for
topology events.  You can use this framework to collect information
about the network topology and install rules to implement shortest
path switching.
"""
from heapq import *
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_0

from ryu.topology import event, switches
import ryu.topology.api as topo

from ryu.lib.packet import packet, ether_types
from ryu.lib.packet import ethernet, arp, icmp

from ofctl_utils import OfCtl, VLANID_NONE, OfCtl_v1_3

from topo_manager_example import TopoManager


class ShortestPathSwitching(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(ShortestPathSwitching, self).__init__(*args, **kwargs)

        self.tm = TopoManager()

    @set_ev_cls(event.EventSwitchEnter)
    def handle_switch_add(self, ev):
        """
        Event handler indicating a switch has come online.
        """
        switch = ev.switch

        self.logger.warn("Added Switch switch%d with ports:", switch.dp.id)
        for port in switch.ports:
            self.logger.warn("\t%d:  %s", port.port_no, port.hw_addr)
        
        # TODO:  Update network topology and flow rules
        self.tm.add_switch(switch)
        self.display_topo()
        # in this project no new switched would be added
        # should be dealt with in the process of enabling ports
        # self.calc_dijkstra()
        # self.remove_all_rules()
        # self.install_all_rules()

    @set_ev_cls(event.EventSwitchLeave)
    def handle_switch_delete(self, ev):
        """
        Event handler indicating a switch has been removed
        """
        switch = ev.switch

        self.logger.warn("Removed Switch switch%d with ports:", switch.dp.id)
        for port in switch.ports:
            self.logger.warn("\t%d:  %s", port.port_no, port.hw_addr)

        # Delete forwarding rules
        for key in self.tm.switches_dev.keys():
            if key.get_dpid() == switch.dp.id:
                for v in self.tm.switches_dev[key]:
                    print("Removing {}".format(v.get_mac()))
                    self.delete_forwarding_rule(key.get_dp(), v.get_mac())
        # Delete device
        self.tm.delete_switch(switch)
        self.display_topo()

        # TODO:  Update network topology and flow rules
        # equivalent to disabling all ports of the switch
        self.calc_dijkstra()
        self.remove_all_rules()
        self.install_all_rules()

    def add_forwarding_rule(self, datapath, dl_dst, port):
        ofctl = OfCtl.factory(datapath, self.logger)
        actions = [datapath.ofproto_parser.OFPActionOutput(port)] 
        
        ofctl.set_flow(cookie=0, priority=0,
            dl_type=ether_types.ETH_TYPE_IP,
            dl_vlan=VLANID_NONE,
            dl_dst=dl_dst,
            actions=actions)

    def delete_forwarding_rule(self, datapath, dl_dst):
        ofctl = OfCtl.factory(datapath, self.logger)
        match = datapath.ofproto_parser.OFPMatch(dl_dst=dl_dst)
        ofctl.delete_flow(cookie=0, priority=0, match=match)


    @set_ev_cls(event.EventHostAdd)
    def handle_host_add(self, ev):
        """
        Event handler indiciating a host has joined the network
        This handler is automatically triggered when a host sends an ARP response.
        """
        host = ev.host
        self.logger.warn("Host Added:  %s (IPs:  %s) on switch%s/%s (%s)",
                          host.mac, host.ipv4,
                         host.port.dpid, host.port.port_no, host.port.hw_addr)
        
        # TODO:  Update network topology and flow rules
        self.tm.add_host(host)
        self.display_topo()
        # for dp in self.tm.switches:
        #     if dp.get_dpid() == host.port.dpid:
        #         self.add_forwarding_rule(dp.get_dp(), host.mac, host.port.port_no)
        self.calc_dijkstra()
        self.remove_all_rules()
        self.install_all_rules()

    @set_ev_cls(event.EventLinkAdd)
    def handle_link_add(self, ev):
        """
        Event handler indicating a link between two switches has been added
        """
        link = ev.link
        src_port = ev.link.src
        dst_port = ev.link.dst
        self.logger.warn("Added Link:  switch%s/%s (%s) -> switch%s/%s (%s)",
                         src_port.dpid, src_port.port_no, src_port.hw_addr,
                         dst_port.dpid, dst_port.port_no, dst_port.hw_addr)
        self.tm.add_link(link)
        self.display_topo()
        # TODO:  Update network topology and flow rules
        # compute the set of {(dp,dl_dst)} that is affected by adding this link.
        # for each (dp,dl_dst)
        # remove the out-dated forwarding rules
        # add new forwarding rules
        self.calc_dijkstra()
        self.remove_all_rules()
        self.install_all_rules()

    @set_ev_cls(event.EventLinkDelete)
    def handle_link_delete(self, ev):
        """
        Event handler indicating when a link between two switches has been deleted
        """
        link = ev.link
        src_port = link.src
        dst_port = link.dst

        self.logger.warn("Deleted Link:  switch%s/%s (%s) -> switch%s/%s (%s)",
                          src_port.dpid, src_port.port_no, src_port.hw_addr,
                          dst_port.dpid, dst_port.port_no, dst_port.hw_addr)
        self.tm.delete_link(link)
        self.display_topo()
        # TODO:  Update network topology and flow rules
        # compute the set of {(dp,dl_dst)} that is affected by deleting this link.
        # for each (dp,dl_dst)
        # remove the out-dated forwarding rule(s
        # add new forwarding rules

        self.calc_dijkstra()
        self.remove_all_rules()
        self.install_all_rules()
        

    @set_ev_cls(event.EventPortModify)
    def handle_port_modify(self, ev):
        """
        Event handler for when any switch port changes state.
        This includes links for hosts as well as links between switches.
        """
        port = ev.port
        self.logger.warn("Port Changed:  switch%s/%s (%s):  %s",
                         port.dpid, port.port_no, port.hw_addr,
                         "UP" if port.is_live() else "DOWN")

        # TODO:  Update network topology and flow rules
        # update links attached to the port
        # if not .is_alive(): remove attached link from graph
        # if .is_alive() and connected_to.is_alive(): restore attached link
        # similar to adding/deleting links
        
        # self.remove_all_rules()
        # self.calc_dijkstra()
        # self.install_all_rules()
        
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        """
       EventHandler for PacketIn messages
        """
        msg = ev.msg

        # In OpenFlow, switches are called "datapaths".  Each switch gets its own datapath ID.
        # In the controller, we pass around datapath objects with metadata about each switch.
        dp = msg.datapath

        # Use this object to create packets for the given datapath
        ofctl = OfCtl.factory(dp, self.logger)

        in_port = msg.in_port
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_ARP:
            arp_msg = pkt.get_protocols(arp.arp)[0]

            if arp_msg.opcode == arp.ARP_REQUEST:

                self.logger.warning("Received ARP REQUEST on switch%d/%d:  Who has %s?  Tell %s",
                                    dp.id, in_port, arp_msg.dst_ip, arp_msg.src_mac)
                source_dp = dp.id
                target = None
                for k in self.tm.switches_dev.keys():
                    if target == None:
                        for v in self.tm.switches_dev[k]:   
                            if v.get_ips()[0] == arp_msg.dst_ip:
                                target = v
                                target_dp = k.get_dpid()
                                break
                    else:
                        break
                if target != None:
                    
                # TODO:  Generate a *REPLY* for this request based on your switch state
                    ofctl.send_arp(vlan_id=VLANID_NONE,
                                arp_opcode=arp.ARP_REPLY,
                                dst_mac=arp_msg.src_mac,
                                sender_mac=target.get_mac(),
                                sender_ip=arp_msg.dst_ip,
                                target_mac=arp_msg.src_mac,
                                target_ip=arp_msg.src_ip,
                                src_port=ofctl.dp.ofproto.OFPP_CONTROLLER,
                                output_port=in_port)
                # Here is an example way to send an ARP packet using the ofctl utilities
                    self.display_shortest_path(source_dp, target_dp)
    def remove_all_rules(self):
        for switch in self.tm.switches:
            dp = switch.get_dp()
            for host in self.tm.hosts:
                self.delete_forwarding_rule(datapath=dp,dl_dst=host.get_mac())

    def install_all_rules(self):
        global mac
        for host in self.tm.hosts:
            for dp in self.tm.switches:
                if dp.get_dpid() == host.get_port().dpid:
                    self.add_forwarding_rule(dp.get_dp(), host.get_mac(), host.get_port().port_no)
        for switch1 in self.tm.switches:
            dp1 = switch1.get_dp()
            for switch2 in self.tm.switches:
                dp2 = switch2.get_dp()
                if not dp1==dp2:
                    if switch2 in self.tm.switches_dev.keys():
                        hosts = self.tm.switches_dev[switch2]
                        for host in hosts:
                            dl_dst = host.get_mac()
                            self.add_forwarding_rule(dp1, dl_dst, mac[dp1.id][dp2.id])

    def calc_dijkstra(self):
        global dis, mac
        dis = {}
        mac = {}
        for sw1 in self.tm.switches:
            dis[sw1.get_dpid()] = {}
            mac[sw1.get_dpid()] = {}
            mac[sw1.get_dpid()][sw1.get_dpid()] = 0
            for sw2 in self.tm.switches:
                dis[sw1.get_dpid()][sw2.get_dpid()] = 1<<30
        for src_sw in self.tm.switches:
            dis[src_sw.get_dpid()][src_sw.get_dpid()] = 0
            heap = [(dis[src_sw.get_dpid()][src_sw.get_dpid()], src_sw.get_dpid())]
            heapify(heap)
            while(len(heap) > 0):
                top_element = heappop(heap)
                cur_sw = top_element[1]
                if not (cur_sw in self.tm.links.keys()):
                    continue
                for edge in self.tm.links[cur_sw]:
                    dst_sw = edge[0].dpid
                    port_no = edge[1].port_no
                    edge_cost = edge[2]
                    if dis[src_sw.get_dpid()][dst_sw] > dis[src_sw.get_dpid()][cur_sw] + edge_cost:
                        dis[src_sw.get_dpid()][dst_sw] = dis[src_sw.get_dpid()][cur_sw] + edge_cost
                        if(cur_sw == src_sw.get_dpid()):
                            mac[src_sw.get_dpid()][dst_sw] = port_no
                        else:
                            mac[src_sw.get_dpid()][dst_sw] = mac[src_sw.get_dpid()][cur_sw]
                        heappush(heap, (dis[src_sw.get_dpid()][dst_sw], dst_sw))
        # for sw1 in self.tm.switches:
        #     for sw2 in self.tm.switches:
        #        self.logger.warn("DIS %d-%d: %d PORT: %s", sw1.get_dpid(), sw2.get_dpid(), dis[sw1.get_dpid()][sw2.get_dpid()], mac[sw1.get_dpid()][sw2.get_dpid()])
    def display_topo(self):
        self.logger.warning("================Topology================")
        for sw in self.tm.switches:
            self.logger.warning("Switch {}".format(sw.get_dpid()))
            self.logger.warning("Devices:")
            if sw in self.tm.switches_dev.keys():
                for h in self.tm.switches_dev[sw]:
                   self.logger.warning("Device: IP: {} mac: {} on port {}".format(h.get_ips(), h.get_mac(), h.get_port().port_no))
            self.logger.warning("Edges:")
            if sw.get_dpid() in self.tm.links.keys():
                for v in self.tm.links[sw.get_dpid()]:
                    st, en = v[0], v[1]
                    self.logger.warn("switch{}/{} ({}) -> switch{}/{} ({})"
                                        .format(en.dpid, en.port_no, en.hw_addr,
                                                st.dpid, st.port_no, st.hw_addr,
                                                ))
       
    def display_shortest_path(self, src_dpid, dst_dpid):
        self.logger.warn("Path from switch {} to swtich {}".format(src_dpid, dst_dpid))
        cur_dpid = src_dpid
        self.logger.warn("{}".format(cur_dpid))
        while cur_dpid != dst_dpid:
            self.logger.warn('->')
            nxt_port = mac[cur_dpid][dst_dpid]
            for e in self.tm.links[cur_dpid]:
                dst,src  = e[0], e[1]
                if src.port_no == nxt_port:
                    self.logger.warn("{}".format(dst.dpid))
                    cur_dpid = dst.dpid
                    break
            
        self.logger.warn("Done")