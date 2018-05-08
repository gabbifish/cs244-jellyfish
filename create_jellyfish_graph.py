import argparse
import json
import networkx as nx
from networkx.readwrite import json_graph
from collections import defaultdict
import random

''' Builds topology from algorithm described in paper '''
def build_from_algorithm(nswitches=3, nhosts=3, k=3, r=1):
    nPortsUsed = defaultdict(int) # switch => num ports that have been connected to a link
    switches = ['s' + str(i) for i in range(nswitches)]
    hosts = ['h' + str(i) for i in range(nhosts)]

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
                # self.addLink(h, s)
                # Add links to graph adjacency list
                update_adj_list(adj_list, h ,s)
                update_adj_list(adj_list, s, h)
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
            # self.addLink(s1, s2)
            # Add links to graph adjacency list
            update_adj_list(adj_list, s1, s2)
            update_adj_list(adj_list, s2, s1)
            # print s1, "is connected to", s2
            nPortsUsed[s1] += 1
            nPortsUsed[s2] += 1

    return adj_list

def update_adj_list(adj_list, v1, v2):
    adj_list.setdefault(v1, [])
    adj_list[v1].append(v2)

def build_from_networkx(G):
    # nodes -> list of neighbors
    adj_dict = {node: list(G.neighbors(node)) for node in G.nodes()}

    return adj_dict

def build_port_map(adj_dict):
    # Map of form port_map[src][dst] = port used by src to talk to dst.
    port_map = defaultdict(lambda:defaultdict(lambda:None))

    # Count of ports used in a switch
    ports_used = defaultdict(lambda:0)

    # connect every switch to a host. Each connection is on sequentially allocated
    # ports each starting at 2. 
    for node in adj_dict.keys():
        switch = 's' + str(node)
        # host_ip = "10.1.%s.0" % node
        # h = self.addHost('h' + node, ip=host_ip)
        # # self.addLink(s, h, port1=0, port2=0)
        # self.addLink(s, h)
        host = 'h' + str(node)
        ports_used[switch] += 1
        port_map[switch][host] = ports_used[switch]

    # connect switches to each other
    connected_switches = set()
    for node, neighbors in adj_dict.iteritems():
        s = 's' + str(node)
        for i in neighbors:
            n = 's' + str(i)
            if (s, n) not in connected_switches \
                    and (n, s) not in connected_switches:
                connected_switches.add((s, n))
                ports_used[s] += 1
                ports_used[n] += 1
                port_map[s][n] = ports_used[s]
                port_map[n][s] = ports_used[n]
    
    return port_map

def create_graph_json():
    # adj = build_from_algorithm()
    G = nx.random_regular_graph(d=3, n=14)
    adj = build_from_networkx(G)
    #port_map = build_port_map(adj)

    # Output adjacency list in json format into temp file.
    with open('graph.json', 'w') as fp:
        json.dump(adj, fp)

    adj_data = json_graph.adjacency_data(G)
    with open('nxgraph.json', 'w') as fp:
        json.dump(adj_data, fp)
        
    # with open('port_map.json', 'w') as fp:
    #     json.dump(port_map, fp)
        
create_graph_json()
