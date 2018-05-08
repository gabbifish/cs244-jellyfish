import os
import sys
import random
import json
from collections import defaultdict
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.node import OVSController
from mininet.node import Controller
from mininet.node import RemoteController
from mininet.cli import CLI
sys.path.append("../../")
from pox.ext.jelly_pox import JELLYPOX
from subprocess import Popen, PIPE
from time import sleep
import itertools

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b) 

def byteify(input):
    if isinstance(input, dict):
        return {byteify(key): byteify(value)
                for key, value in input.iteritems()}
    elif isinstance(input, list):
        return [byteify(element) for element in input]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return input

class JellyFishTop(Topo):
    ''' Builds topology '''
    def build(self):
        self.build_from_json()
        #self.build_from_algorithm()

    ''' Builds topology from given json file of graph adjacency list'''
    def build_from_json(self, filename='graph.json'):
        with open(filename, 'r') as fp:
            adj_dict = byteify(json.load(fp))
            
            linkopts = dict(bw=1)

            # add all switches. The first port will always connect to a host.
            for node in adj_dict.keys():
                switch_ip = ip="10.0.0.%s" % node
                s = self.addSwitch('s' + str(node))

            # connect every switch to a host. Each connection is on sequentially allocated
            # ports each starting at 2. 
            for node in adj_dict.keys():
                s = 's' + node
                host_ip = "10.1.%s.0" % node
                h = self.addHost('h' + node, ip=host_ip)
                self.addLink(h, s, port1=1025, port2=1)
                # self.addLink(h, s)

            # connect switches to each other
            connected_switches = set()
            for node, neighbors in adj_dict.iteritems():
                s = 's' + node
                for i in neighbors:
                    n = 's' + str(i)
                    if (s, n) not in connected_switches \
                            and (n, s) not in connected_switches:

                        opts = { 'bw': .1}
                        self.addLink(s, n, port1=int(i)+2, port2=int(node)+2, opts=opts)
                        # self.addLink(s, n)
                        connected_switches.add((s, n))

    ''' Builds topology from algorithm described in paper '''
    def build_from_algorithm(self, nswitches=3, nhosts=3, k=3, r=1):
        nPortsUsed = defaultdict(int) # switch => num ports that have been connected to a link
        switches = [self.addSwitch('s' + str(i), ip="10.0.0.%d" % i) for i in range(nswitches)]
        hosts = [self.addHost('h' + str(i), ip="10.1.%d.0" % i, mac="00:00:00:%0.2X:00:00" % i) for i in range(nhosts)]

        # Dict of vertices to the list of vertices they connect to; this is a graph adjacency list.
        # We ulitamtely output this representation of the graph in json, so another script can
        # compute edge popularity among paths.
        adj_list = {}

        # Connect each host to one switch
        for h in hosts:
            while True:
                s = random.choice(switches)
                nPorts = nPortsUsed[s]
                if r - nPorts > 0:
                    self.addLink(h, s)
                    # Add links to graph adjacency list
                    self.update_adj_list(adj_list, h ,s)
                    self.update_adj_list(adj_list, s, h)
                    nPortsUsed[s] = nPorts + 1
                    # print h, "is connected to", s
                    break

        # Connect switches to each other
        linkPairs = set()

        switchPairs = []
        for idx, s1 in enumerate(switches):
            for idx2 in range(idx + 1, len(switches)):
                switchPairs.append((s1, switches[idx2]))

        # random.shuffle(switchPairs)
        for s1, s2 in switchPairs:
            if nPortsUsed[s1] < k and nPortsUsed[s2] < k:
                self.addLink(s1, s2)
                # Add links to graph adjacency list
                self.update_adj_list(adj_list, s1, s2)
                self.update_adj_list(adj_list, s2, s1)
                # print s1, "is connected to", s2
                nPortsUsed[s1] += 1
                nPortsUsed[s2] += 1

        # Output adjacency list in json format into temp file.
        # with open('jellyfish_graph_adj_list.json', 'w') as fp:
            # json.dump(adj_list, fp)

    def update_adj_list(self, adj_list, v1, v2):
        adj_list.setdefault(v1, [])
        adj_list[v1].append(v2)

def iperf_baseline(hosts):
    # runs flows from 1 host to another in isolation
    for client, server in pairwise(hosts):
        print "  getting baseline from %s to %s" % (client.name, server.name)
        for i in range(5):
            output_file = "iperf_baseline_%s_to_%s_%d.txt" % (
                client.name, server.name, i)
            server_cmd = "iperf -s -p %d &" % (5555)
            client_cmd = "iperf -c %s -p %d -t %d > %s &" % (server.IP(),
                5555, 5, output_file)
            
            print "    on %s running command: %s" % (server.name, server_cmd)
            server.sendCmd(server_cmd)
            # wait until command has executed
            server.waitOutput(verbose=True)
            print "    on %s running command: %s" % (client.name, client_cmd)
            client.sendCmd(client_cmd)
            client.waitOutput(verbose=True)

            # wait until processes are completely done
            # only a pair of hosts is tested at a time
            pid = int(client.cmd('echo $!'))
            client.cmd('wait', pid)
            server.cmd('kill -9 %iperf')
            server.cmd('wait')

def iperf_test(hosts, test_type, index=0):
    # host to pid of the iperf client process
    host_to_pid = {}
    for client, server in pairwise(hosts):
        print "  testing throughput from %s to %s" % (client.name, server.name)

        output_file = "iperf_%s_%s_to_%s_%d.txt" % (test_type,
            client.name, server.name, index)
        server_cmd = "iperf -s -p %d &" % (5555)
        client_cmd = "iperf -c %s -p %d %s -t %d > %s &" % (server.IP(),
            5555, ("-P 8" if test_type.endswith("8flow") else ""), 5, output_file)
        
        print "    on %s running command: %s" % (server.name, server_cmd)
        server.sendCmd(server_cmd)
        # wait until command has executed
        server.waitOutput(verbose=True)
        print "    on %s running command: %s" % (client.name, client_cmd)
        client.sendCmd(client_cmd)
        client.waitOutput(verbose=True)
        pid = int(client.cmd('echo $!'))
        host_to_pid[client] = pid

    print "Waiting for iperf tests to finish..."
    for host, pid in host_to_pid.iteritems():
        host.cmd('wait', pid)

    print "Killing all iperf instances..."
    # need to kill iperf instances so we can rerun these tests on the same mininet
    for client, server in pairwise(hosts):
        server.cmd( "kill -9 %iperf" )
        # Wait for iperf server to terminate
        server.cmd( "wait" )

def experiment(net):
    print "Starting mininet..."
    net.start()
    # sleep to wait for switches to come up and connect to controller
    sleep(3)

    num_runs = 5

    # run tests to estimate link capacity
    print "Running tests to estimate link capacity"
    iperf_baseline(net.hosts)

    # TODO: figure out how to run ecmp and 8 shortest path experiments in same script
    # print "Running TCP 1-flow experiment on jellyfish"
    # for i in range(0, num_runs):
    #     iperf_test(net.hosts, "shortest8_1flow", i)

    # print "Running TCP 8-flow experiment on jellyfish"
    # for i in range(0, num_runs):
    #     iperf_test(net.hosts, "shortest8_8flow", i)
    
    # print "Running TCP 1-flow experiment on jellyfish"
    # for i in range(0, num_runs):
    #     iperf_test(net.hosts, "ecmp_1flow", i)

    # print "Running TCP 8-flow experiment on jellyfish"
    # for i in range(0, num_runs):
    #     iperf_test(net.hosts, "ecmp_8flow", i)
   
    #CLI(net)
    # net.pingAll()
    print "Done. Shutting down mininet."
    net.stop()

TOPOS = {'JellyTopo' : (lambda : JellyFishTop())}
def main():
	topo = JellyFishTop()
	net = Mininet(topo=topo, host=CPULimitedHost, link = TCLink, controller=JELLYPOX)
	experiment(net)

if __name__ == "__main__":
	main()

