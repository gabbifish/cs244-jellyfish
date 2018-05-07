# Copyright 2012 James McCauley
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain arp_req copy of the License at:
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
This component is for use with the OpenFlow tutorial.

It acts as arp_req simple hub, but can be modified to act like an L2
learning switch.

It's roughly similar to the one Brandon Heller did for NOX.
"""

from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.packet.ethernet import ethernet, ETHER_BROADCAST, EthAddr
from pox.lib.packet.ipv4 import IPAddr
from pox.lib.packet.arp import arp
from pox.lib.util import dpid_to_str, str_to_bool
from collections import defaultdict

from networkx.readwrite import json_graph
import networkx as nx
import json
import random
import itertools

log = core.getLogger()

# Placeholder for graph representation, read from graph.json in 
# launch().
G = None

# def k_shortest_paths(graph, source, target, k=8):
#   return list(itertools.islice(
#       nx.shortest_simple_paths(graph, source, target), k))

# Adjacency map.  [sw1][sw2] -> port from sw1 to sw2
# adjacency = defaultdict(lambda:defaultdict(lambda:None))
# # adjacency = [1:[0,2]]
# with open('pox/ext/port_map.json', 'r') as fp:
#   adjacency = json.load(fp)
#   print adjacency

# Switches we know of.  [dpid] -> Switch and [id] -> Switch
switches_by_dpid = {}
switches_by_id = {}

# [sw1][sw2] -> (distance, intermediate)
path_map = defaultdict(lambda:defaultdict(lambda:(None,None)))

def dpid_to_mac (dpid):
  return EthAddr("%012x" % (dpid & 0xffFFffFFffFF,))

def ipinfo (ip):
  parts = [int(x) for x in str(ip).split('.')]
  host_or_switch = parts[1]
  host_num = parts[2]
  sw_num = parts[3]
  return host_or_switch, host_num, sw_num

class TopoSwitch (object):
  """
  A TopoSwitch object is created for each switch that connects.
  A Connection object for that switch is passed to the __init__ function.
  """

  def __init__ (self, connection):
    # Keep track of the connection to the switch so that we can
    # send it messages!
    self.connection = connection
    self.ports = None
    self.dpid = None
    self._id = None
    self.network = None
    self._install_flow = False
    self.mac = None

    # For each switch, we map IP addresses to MAC addresses using ARP.
    self.ip_to_mac = {}

    # # These are "fake gateways" -- we'll answer ARPs for them with MAC
    # # of the switch they're connected to.
    # self.fakeways = set([])

    # This binds our PacketIn event listener
    connection.addListeners(self)

    # Use this table to keep track of which ethernet address is on
    # which switch port (keys are MACs, values are ports).
    self.mac_to_port = {}

  # Can use connect to sent ARP through each port to learn neighboring ports?
  # Send out ARP for each neighboring IP (which we already know for each node).
  def connect (self, connection):
    log.info("New connection")
    if connection is None:
      log.warn("Can't connect to nothing")
      return
    if self.dpid is None:
      self.dpid = connection.dpid

    assert self.dpid == connection.dpid
    if self.ports is None:
      self.ports = connection.features.ports
      log.info(self.ports)

    # Set switch ID.
    if self._id is None:
      if self.dpid not in switches_by_id and self.dpid <= 254:
        self._id = self.dpid
      else:
        self._id = 0
      switches_by_id[self._id] = self

    self.network = IPAddr("10.0.0.%s" % (self._id,))
    log.info("network is %s", self.network)
    self.mac = dpid_to_mac(self.dpid)
    log.info("mac is %s", self.mac)

  def resend_packet (self, packet_in, out_port):
    """
    Instructs the switch to resend arp_req packet that it had sent to us.
    "packet_in" is the ofp_packet_in object the switch had sent to the
    controller due to arp_req table-miss.
    """
    msg = of.ofp_packet_out()
    msg.data = packet_in

    # Add an action to send to the specified port
    action = of.ofp_action_output(port = out_port)
    msg.actions.append(action)

    # Send message to switch
    self.connection.send(msg)

  def act_like_hub (self, packet, packet_in):
    """
    Implement hub-like behavior -- send all packets to all ports besides
    the input port.
    """
    # We want to output to all ports -- we do that using the special
    # OFPP_ALL port as the output port.  (We could have also used
    # OFPP_FLOOD.)
    self.resend_packet(packet_in, of.OFPP_ALL)

    # Note that if we didn't get arp_req valid buffer_id, arp_req slightly better
    # implementation would check that we got the full data before
    # sending it (len(packet_in.data) should be == packet_in.total_len)).


  def act_like_switch (self, packet, packet_in):
    """
    Implement switch-like behavior.
    """
    # log.info(packet)
    # self.resend_packet(packet_in, 2)
    switch_name = "s" + str(self._id)

    # if switch != id number of destination, this switch is not directly
    # connected to dst host. Forward out correct port.
    ipp = packet.find('ipv4')
    dst_host = ipinfo(ipp.dstip)[1]

    # Default: this switch is connected to our destination port.
    # Port 1 always connects to host, by our design. 
    # TODO: THIS DOESN'T GET THE PACKET FROM SWITCH TO HOST???
    outport = of.OFPP_IN_PORT

    # Other case: this switch is not connected to destination port, will have
    # to forward to other switch.
    if dst_host != self._id:
      # TODO: PUT NEXT-HOP SELECTION CODE HERE!!! THIS WILL USE THE ALGORITHMS!
      # Right now, since we are using a triangle topology and all switches are connected,
      # we know that sending the packet to sX will send it to hX.
      outport = dst_host + 2

    log.info("forwarding out of switch %d using port %d", self._id, outport)

    self.resend_packet(packet_in, outport) 
    """
    # DELETE THIS LINE TO START WORKING ON THIS (AND THE ONE BELOW!) #

    # Here's some psuedocode to start you off implementing arp_req learning
    # switch.  You'll need to rewrite it as real Python code.

    # Learn the port for the source MAC
    self.mac_to_port[]

    # use dst IP to get DST Mac to get necessary port
    if the port associated with the destination MAC of the packet is known:
      # Send packet out the associated port
      self.resend_packet(packet_in, ...)

      # Once you have the above working, try pushing arp_req flow entry
      # instead of resending the packet (comment out the above and
      # uncomment and complete the below.)

      log.debug("Installing flow...")
      # Maybe the log statement should have source/destination/port?

      #msg = of.ofp_flow_mod()
      #
      ## Set fields to match received packet
      #msg.match = of.ofp_match.from_packet(packet)
      #
      #< Set other fields of flow_mod (timeouts? buffer_id?) >
      #
      #< Add an output action, and send -- similar to resend_packet() >

    else:
      # Flood the packet out everything but the input port
      # This part looks familiar, right?
      self.resend_packet(packet_in, of.OFPP_ALL)
    """

  def _mac_learn (self, mac, ip):
    if self.ip_to_mac.get(ip) != mac:
      self.ip_to_mac[ip] = mac
      return True
    return False

  def _arp_response_pkt (self, arp_req, packet):
    r = arp()
    r.hwtype = arp_req.hwtype
    r.prototype = arp_req.prototype
    r.hwlen = arp_req.hwlen
    r.protolen = arp_req.protolen
    r.opcode = arp_req.REPLY
    r.hwdst = arp_req.hwsrc
    r.protodst = arp_req.protosrc
    r.protosrc = arp_req.protodst
    r.hwsrc = self.ip_to_mac.get(arp_req.protodst, self.mac)
    e = ethernet(type=packet.type, src=dpid_to_mac(self.dpid),
                            dst=arp_req.hwsrc)
    e.payload = r
    log.info("%s answering ARP for %s with MAC %s" % (dpid_to_str(self.dpid), str(r.protosrc), r.hwsrc))
    return e

  def _arp_request_pkt (self, req_sw):
    r = arp()
    r.hwtype = arp.HW_TYPE_ETHERNET
    r.prototype = arp.PROTO_TYPE_IP
    r.hwlen = 6
    r.protolen = 4
    r.opcode = arp.REQUEST
    r.hwdst = self.mac
    r.protodst = IPAddr("10.0.0.%s" % (req_sw,))
    r.protosrc = self.network
    r.hwsrc = self.mac
    e = ethernet(type=ethernet.ARP_TYPE, src=dpid_to_mac(self.dpid),
                            dst=ETHER_BROADCAST)
    e.payload = r
    log.info("%s making ARP request for %s" % (dpid_to_str(self.dpid), str(r.protodst)))
    return e

  # def _arp_send (self, e, msg, inport):
  #   msg = of.ofp_packet_out()
  #   msg.data = e.pack()
  #   msg.actions.append(of.ofp_action_output(port = of.OFPP_IN_PORT))
  #   msg.in_port = inport
  #   event.connection.send(msg)

  def _handle_PacketIn (self, event):
    """
    Handles packet in messages from the switch. Have to handle case when
    packet is recieved but all switches aren't up yet. Sleep?
    """
    packet_in = event.ofp # The actual ofp_packet_in message.
    
    packet = event.parsed # This is the parsed packet data.
    if not packet.parsed:
      log.warning("%i %i ignoring unparsed packet", dpid, inport)
      return
  
    if packet.type == ethernet.LLDP_TYPE:
        # Ignore LLDP packets
        return

    self.act_like_hub(packet, packet_in)

    arpp = packet.find('arp')
    if arpp is not None:
      # Learn IP to MAC address mapping.
      if self._mac_learn(packet.src, arpp.protosrc):
        log.info("switch %s learned %s -> %s by ARP", self.dpid, arpp.protosrc, packet.src)
      # dpid = event.connection.dpid
      inport = event.port 
      if packet.src not in self.mac_to_port:
        self.mac_to_port[packet.src] = inport
      # Respond to ARP request if appropriate.
      if arpp.opcode == arp.REQUEST and ipinfo(arpp.protosrc)[0] == 1:
        log.info("ARP request for dst %s from source %s recieved by switch %d on port %d", arpp.protodst, arpp.protosrc, self.dpid, inport)
        e = self._arp_response_pkt(arpp, packet)
        msg = of.ofp_packet_out()
        msg.data = e.pack()
        msg.actions.append(of.ofp_action_output(port = of.OFPP_IN_PORT))
        msg.in_port = inport
        event.connection.send(msg)

    ipp = packet.find('ipv4')
    if ipp is not None:
      log.info("IP packet received by switch %d on port %d. src is %s, dst is %s", self._id, event.port, ipp.srcip, ipp.dstip)
      log.info("switch %s has mac_to_port table %s", self.dpid, self.mac_to_port)
      # Need to send out ARP requests to figure out next hop. 
      # Namely, which outgoing port corresponds to your next hop?
      # for i in adjacency[self.dpid]:
        # e = self._arp_response_pkt(arpp, i)
        # msg = of.ofp_packet_out()
        # msg.data = e.pack()
        # msg.actions.append(of.ofp_action_output(port = of.OFPP_ALL))
        # msg.in_port = inport
        # event.connection.send(msg)
      # Only forward IP packets, not ARP.
      # self.act_like_hub(packet, packet_in)
      self.act_like_switch(packet, packet_in)

def launch ():
  """
  Starts the component. Listens to all up events. 
  """
  def start_switch (event):
    log.info("switch %s has come up" % event.dpid)
    log.info(event.connection.ports)
    sw = switches_by_dpid.get(event.dpid)

    if sw is None:
      # New switch
      sw = TopoSwitch(event.connection)
      switches_by_dpid[event.dpid] = sw
      sw.connect(event.connection)
    else:
      sw.connect(event.connection)
  core.openflow.addListenerByName("ConnectionUp", start_switch)
