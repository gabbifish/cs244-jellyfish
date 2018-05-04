# Copyright 2012 James McCauley
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
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

It acts as a simple hub, but can be modified to act like an L2
learning switch.

It's roughly similar to the one Brandon Heller did for NOX.
"""

from pox.core import core
import pox.openflow.libopenflow_01 as of
import pox.lib.packet as pkt
from pox.lib.packet import *

from networkx.readwrite import json_graph
import networkx as nx
import json
import random
import itertools

log = core.getLogger()

with open('pox/ext/nxgraph.json', 'r') as fp:
  data = json.load(fp)
G = json_graph.adjacency_graph(data)

def k_shortest_paths(graph, source, target, k=8):
  return list(itertools.islice(
      nx.shortest_simple_paths(graph, source, target), k))

def get_out_port(src, dst):
  if src == dst:
    # the destination is the host attached to this switch
    # all switches attach to their host at port 0
    return 0

  # choose one random path out of 8 shortest paths to traverse
  paths = k_shortest_paths(G, src, dst)
  path = random.choice(paths)
  next_hop = path[1]

  # switch i is connected to this switch via port i+1
  return next_hop + 1

class Tutorial (object):
  """
  A Tutorial object is created for each switch that connects.
  A Connection object for that switch is passed to the __init__ function.
  """
  def __init__ (self, connection):
    # Keep track of the connection to the switch so that we can
    # send it messages!
    self.connection = connection

    # This binds our PacketIn event listener
    connection.addListeners(self)

    # Use this table to keep track of which ethernet address is on
    # which switch port (keys are MACs, values are ports).
    self.mac_to_port = {}

    # Pseudo-routing table of next-hop IP addresses to outgoing port
    self.ip_to_port = {}


  def resend_packet (self, packet_in, out_port):
    """
    Instructs the switch to resend a packet that it had sent to us.
    "packet_in" is the ofp_packet_in object the switch had sent to the
    controller due to a table-miss.
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

    # Note that if we didn't get a valid buffer_id, a slightly better
    # implementation would check that we got the full data before
    # sending it (len(packet_in.data) should be == packet_in.total_len)).


  def act_like_switch (self, packet, packet_in, name):
    """
    Implement switch-like behavior.
    """

    # DELETE THIS LINE TO START WORKING ON THIS (AND THE ONE BELOW!) #

    # Here's some psuedocode to start you off implementing a learning
    # switch.  You'll need to rewrite it as real Python code.

    # Learn the port for the source MAC
    self.mac_to_port[packet.src] = packet_in.in_port

    # arp = packet.find('arp')
    # if arp is not None:
    #   # for now, ignore arp packets since we know the entire topology
    #   return

    ipv6 = packet.find('ipv6')
    if ipv6 is not None:
      srcip = ipv6.srcip
      dstip = ipv6.dstip
      dst_id = int(str(dstip).split(":")[-1], 16)
      log.info("srcipv6 " + str(srcip))
      log.info("dstipv6 " + str(dstip))

    ipv4 = packet.find('ipv4')
    if ipv4 is not None:
      srcip = ipv4.srcip
      dstip = ipv4.dstip
      dst_id = int(str(dstip).split(".")[-1])
      print "srcipv4", srcip
      print "dstipv4", dstip

    # src_id = int(name[1:])
    # if dst_id in G:
    #   log.info("dst_id " + str(dst_id))
    #   out_port = get_out_port(src_id, dst_id)
    #   self.resend_packet(packet_in, out_port)

    #if packet.type == pkt.IP_TYPE:
    ip_packet = packet.payload
    log.info(ip_packet)

    #if the port associated with the destination MAC of the packet is known:
      # Send packet out the associated port
      #self.resend_packet(packet_in, ...)

      # Once you have the above working, try pushing a flow entry
      # instead of resending the packet (comment out the above and
      # uncomment and complete the below.)

      #log.debug("Installing flow...")
      # Maybe the log statement should have source/destination/port?

      #msg = of.ofp_flow_mod()
      #
      ## Set fields to match received packet
      #msg.match = of.ofp_match.from_packet(packet)
      #
      #< Set other fields of flow_mod (timeouts? buffer_id?) >
      #
      #< Add an output action, and send -- similar to resend_packet() >

    #else:
      # Flood the packet out everything but the input port
      # This part looks familiar, right?
      #self.resend_packet(packet_in, of.OFPP_ALL)

    # DELETE THIS LINE TO START WORKING ON THIS #


  def _handle_PacketIn (self, event):
    """
    Handles packet in messages from the switch.
    """

    packet = event.parsed # This is the parsed packet data.
    if not packet.parsed:
      log.warning("Ignoring incomplete packet")
      return

    packet_in = event.ofp # The actual ofp_packet_in message.

    # Comment out the following line and uncomment the one after
    # when starting the exercise.
    # print "Src: " + str(packet.src)
    # print "Dest: " + str(packet.dst)
    # print "Event port: " + str(event.port)
    # #self.act_like_hub(packet, packet_in)
    log.info("packet in")

    name = event.connection.features.ports[0].name
    self.act_like_switch(packet, packet_in, name)



def launch ():
  """
  Starts the component
  """
  def start_switch (event):
    log.debug("Controlling %s" % (event.connection,))
    Tutorial(event.connection)
  core.openflow.addListenerByName("ConnectionUp", start_switch)
