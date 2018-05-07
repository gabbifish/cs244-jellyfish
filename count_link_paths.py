import networkx as nx
import json
import itertools
import random
from collections import defaultdict
import matplotlib
matplotlib.use('AGG')
import matplotlib.pyplot as plt
#import plotly.plotly as py

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

def create_plot(edges_to_npaths, filename):
    y = sorted(edges_to_npaths.values())
    x = list(range(0, len(y)))
    plt.plot(x, y)
    plt.savefig(filename)

def create_figure(kshortest_data, ecmp8_data, ecmp64_data, filename):
    links = kshortest_data.keys()
    kshortest = sorted(kshortest_data.values())
    ecmp8 = sorted([ecmp8_data[link] for link in links])
    ecmp64 = sorted([ecmp64_data[link] for link in links])  
    x = list(range(0, len(links)))
    
    plt.figure()
    plt.plot(x, kshortest, label='k-shortest')
    plt.plot(x, ecmp64, label='ecmp 64')
    plt.plot(x, ecmp8, label='ecmp 8')

    plt.title('Reproduction of Figure 9')
    plt.xlabel("Rank of Link")
    plt.ylabel("# Distinct paths link is on")
    plt.legend(loc='upper left')
    plt.savefig(filename)


#G = create_graph_from_adjlist('jellyfish_graph_adj_list.json')
G = nx.random_regular_graph(d=6, n=686)
kshortest_data = count_distinct_paths(G, k_shortest_paths, 8)
ecmp64_data = count_distinct_paths(G, ecmp, 64)
ecmp8_data = count_distinct_paths(G, ecmp, 8)


# create_plot(kshortest_data, 'kshortest.png')
# create_plot(ecmp8_data, 'ecmp8.png')
# create_plot(ecmp64_data, 'ecmp64.png')
create_figure(kshortest_data, ecmp8_data, ecmp64_data, 'figure9-6degree2.png')

