import lib

import networkx as nx

import time

from matplotlib import pyplot as plt

nodes = lib.fireup_network(range(8800, 8810))

G = nx.DiGraph()

urls = map(lambda x: x.nodeinfo["addr"], nodes)

G.add_nodes_from(urls)

time.sleep(30)

for n in nodes:
    print("mapping ", n)
    peers = n.Client.getPeers(n.nodeinfo)
    addrs = map(lambda x: x["addr"], peers)
    for a in addrs:
        G.add_edge(n.nodeinfo["addr"], a)

nx.draw(G)

plt.show()
