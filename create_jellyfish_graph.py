import argparse
import json
import networkx as nx
from networkx.readwrite import json_graph

G = nx.random_regular_graph(d=2, n=3)

# nodes -> list of neighbors
adj_dict = {node: list(G.neighbors(node)) for node in G.nodes()}

with open('graph.json', 'w') as fp:
    json.dump(adj_dict, fp)

adj_data = json_graph.adjacency_data(G)
with open('nxgraph.json', 'w') as fp:
    json.dump(adj_data, fp)
