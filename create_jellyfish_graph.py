import argparse
import json
import networkx as nx
from networkx.readwrite import json_graph

G = nx.random_regular_graph(d=2, n=3)

# nodes -> list of neighbors
adj_list = {node: list(G.neighbors(node)) for node in G.nodes()}

# adj_list = json_graph.adjacency_data(G)
with open('graph.json', 'w') as fp:
    json.dump(adj_list, fp)
