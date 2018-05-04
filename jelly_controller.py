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
from pox.lib.packet.ethernet import ethernet, ETHER_BROADCAST
from collections import defaultdict

log = core.getLogger()

def ipinfo (ip):
  parts = [int(x) for x in str(ip).split('.')]
  ID = parts[1]
  port = parts[2]
  num = parts[3]
  return switches_by_id.get(ID),port,num

# Adjacency map.  [sw1][sw2] -> port from sw1 to sw2
adjacency = defaultdict(lambda:defaultdict(lambda:None))

# Switches we know of.  [dpid] -> Switch and [id] -> Switch
switches_by_dpid = {}
switches_by_id = {}

# [sw1][sw2] -> (distance, intermediate)
path_map = defaultdict(lambda:defaultdict(lambda:(None,None)))

class Entry (object):
  """
  Not strictly an ARP entry.
  We use the port to determine which port to forward traffic out of.
  We use the MAC to answer ARP replies.
  We use the timeout so that if an entry is older than ARP_TIMEOUT, we
   flood the ARP request rather than try to answer it ourselves.
  """
  def __init__ (self, port, mac):
    self.timeout = time.time() + ARP_TIMEOUT
    self.port = port
    self.mac = mac

  def __eq__ (self, other):
    if type(other) == tuple:
      return (self.port,self.mac)==other
    else:
      return (self.port,self.mac)==(other.port,other.mac)
  def __ne__ (self, other):
    return not self.__eq__(other)

  def isExpired (self):
    if self.port == of.OFPP_NONE: return False
    return time.time() > self.timeout


def dpid_to_mac (dpid):
  return EthAddr("%012x" % (dpid & 0xffFFffFFffFF,))

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
    self._listeners = None
    self._connected_at = None
    self._id = None
    self.subnet = None
    self.network = None
    self._install_flow = False
    self.mac = None

    self.ip_to_mac = {}

    # For each switch, we map IP addresses to Entries
    self.arpTable = {}

    # These are "fake gateways" -- we'll answer ARPs for them with MAC
    # of the switch they're connected to.
    self.fakeways = set([])

    # This binds our PacketIn event listener
    connection.addListeners(self)

    # Use this table to keep track of which ethernet address is on
    # which switch port (keys are MACs, values are ports).
    self.mac_to_port = {}

    # NEED TO MATCH ACTION TABLE TO SWITCH.

  def connect (self, connection):
    log.info("New connection")
    if connection is None:
      log.warn("Can't connect to nothing")
      return
    if self.dpid is None:
      self.dpid = connection.dpid

    # assert self.dpid == connection.dpid
    # if self.ports is None:
    #   self.ports = connection.features.ports
    # self.disconnect()
    # self.connection = connection
    # self._listeners = self.listenTo(connection)
    # self._connected_at = time.time()

    # label = dpid_to_str(connection.dpid)
    # self.log = log.getChild(label)
    # self.log.debug("Connect %s" % (connection,))

    # if self._id is None:
    #   if self.dpid not in switches_by_id and self.dpid <= 254:
    #     self._id = self.dpid
    #   else:
    #     self._id = TopoSwitch._next_id
    #     TopoSwitch._next_id += 1
    #   switches_by_id[self._id] = self

    # self.network = IPAddr("10.%s.0.0" % (self._id,))
    # self.mac = dpid_to_mac(self.dpid)

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
    log.info("switch %s has mac_to_port table %s", self.dpid, self.mac_to_port)
    # We want to output to all ports -- we do that using the special
    # OFPP_ALL port as the output port.  (We could have also used
    # OFPP_FLOOD.)
    self.resend_packet(packet_in, of.OFPP_ALL)

    # Note that if we didn't get a valid buffer_id, a slightly better
    # implementation would check that we got the full data before
    # sending it (len(packet_in.data) should be == packet_in.total_len)).


  def act_like_switch (self, packet, packet_in):
    """
    Implement switch-like behavior.
    """
    # log.info(packet)
    log.info("switch %s has mac_to_port table %s", self.dpid, self.mac_to_port)
    """
    # DELETE THIS LINE TO START WORKING ON THIS (AND THE ONE BELOW!) #

    # Here's some psuedocode to start you off implementing a learning
    # switch.  You'll need to rewrite it as real Python code.

    # Learn the port for the source MAC
    self.mac_to_port[]

    # use dst IP to get DST Mac to get necessary port
    if the port associated with the destination MAC of the packet is known:
      # Send packet out the associated port
      self.resend_packet(packet_in, ...)

      # Once you have the above working, try pushing a flow entry
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
    # if ip.inNetwork(self.network,"255.255.0.0"):
    if self.ip_to_mac.get(ip) != mac:
      self.ip_to_mac[ip] = mac
      # self._send_rewrite_rule(ip, mac)
      return True
    return False

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
  
    arpp = packet.find('arp')
    if arpp is not None:
      if self._mac_learn(packet.src, arpp.protosrc):
        log.info("switch %s learned %s -> %s by ARP", self.dpid, arpp.protosrc,packet.src)
      # dpid = event.connection.dpid
      inport = event.port 
      if packet.src not in self.mac_to_port:
        self.mac_to_port[packet.src] = inport

    # log.info("recieved packet %s" % str(packet))

    # if dpid not in self.arpTable:
    #   # New switch -- create an empty table
    #   self.arpTable[dpid] = {}
    #   # for fake in self.fakeways:
    #   #   self.arpTable[dpid][IPAddr(fake)] = Entry(of.OFPP_NONE,
    #   #    dpid_to_mac(dpid))

    if packet.type == ethernet.LLDP_TYPE:
      # Ignore LLDP packets
      return

    # Flood ARP packets? for now...
    # arp = packet.find('arp')
    # if arp is not None:
    #   self.act_like_hub(packet, packet_in)

    # # But do not flood IP packets!
    # ip = packet.find('ipv4')
    # if ip is not None:
    self.act_like_hub(packet, packet_in)
    # self.act_like_switch(packet, packet_in)

def launch ():
  """
  Starts the component. Listens to all up events. 
  """
  def start_switch (event):
    log.info("switch %s has come up, and has ports" % event.dpid)
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
  # ^ should be register_new
