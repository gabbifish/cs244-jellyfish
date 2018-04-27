import networkx as nx
import json
import itertools
import random
from collections import defaultdict
# matplotlib

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b) 

def create_graph_from_adjlist(filename):
    with open(filename, 'r') as fp:
        adj_dict = json.load(fp)
        adj_list = [node + ' ' + ' '.join(neighbors)
            for node, neighbors in adj_dict.iteritems()]
        return nx.parse_adjlist(adj_list)

def get_hosts(graph):
    return [node for node in G.nodes() if node.startswith('h')]

def k_shortest_paths(graph, source, target, k):
    return list(itertools.islice(
        nx.shortest_simple_paths(graph, source, target), k))

def ecmp(graph, source, target, k):
    return list(itertools.islice(
        nx.all_shortest_paths(graph, source, target), k))

def count_distinct_paths(graph, get_paths_func, k):
    edges_to_npaths = defaultdict(int)
    servers = G.nodes()
    for s1, s2 in pairwise(servers):
        paths = get_paths_func(graph, s1, s2, k)
        for path in paths:
            for n1, n2 in pairwise(path):
                edges_to_npaths[(n1, n2)] += 1
    # todo: fencepost problem, missing last server pair
    return edges_to_npaths

    # hosts = get_hosts(graph)
    # edgesToNumPaths = {}
    # for i, source in enumerate(hosts):
    #     for j in range(i + 1, len(hosts)):
    #         target = hosts[j]
    #         paths = get_paths_func(graph, source, target, k)
    #         for path in paths:
    #             for n1, n2 in pairwise(path):
    #                 if (n1, n2) in edgesToNumPaths:
    #                     edgesToNumPaths[(n1, n2)] += 1
    #                 elif (n2, n1) in edgesToNumPaths:
    #                     edgesToNumPaths[(n2, n1)] += 1
    #                 else:
    #                     edgesToNumPaths[(n1, n2)] = 1
    # return edgesToNumPaths

#G = create_graph_from_adjlist('jellyfish_graph_adj_list.json')
G = nx.random_regular_graph(d=2, n=3)
print count_distinct_paths(G, k_shortest_paths, 8)
print count_distinct_paths(G, ecmp, 8)
print count_distinct_paths(G, ecmp, 64)
