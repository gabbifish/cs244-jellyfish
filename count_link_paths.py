import networkx as nx
import json
import itertools
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

def eight_shortest_paths(graph, source, target):
    return list(itertools.islice(
        nx.shortest_simple_paths(graph, source, target), 8))

def ecmp_8(graph, source, target):
    return list(itertools.islice(
        nx.all_shortest_paths(graph, source, target), 8))

def count_distinct_paths(graph, get_paths_func):
    hosts = get_hosts(graph)
    edgesToNumPaths = {}
    for i, source in enumerate(hosts):
        for j in range(i + 1, len(hosts)):
            target = hosts[j]
            paths = get_paths_func(graph, source, target)
            for path in paths:
                for n1, n2 in pairwise(path):
                    if (n1, n2) in edgesToNumPaths:
                        edgesToNumPaths[(n1, n2)] += 1
                    elif (n2, n1) in edgesToNumPaths:
                        edgesToNumPaths[(n2, n1)] += 1
                    else:
                        edgesToNumPaths[(n1, n2)] = 1
    return edgesToNumPaths


G = create_graph_from_adjlist('jellyfish_graph_adj_list.json')
print count_distinct_paths(G, eight_shortest_paths)
print count_distinct_paths(G, ecmp_8)
