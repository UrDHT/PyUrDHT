import lib

import networkx as nx

import time

from matplotlib import pyplot as plt

nodes = lib.fireup_network(range(55500, 55550))

G = nx.DiGraph()

urls = map(lambda x: x.nodeinfo["addr"], nodes)

G.add_nodes_from(urls)

positions = {}

for i in range(60,0,-1):
    print("Counting Down",i)
    time.sleep(1)

for n in nodes:
    print("mapping ", n)
    try:
        peers = n.Client.getPeers(n.nodeinfo)
        for p in peers:
            G.add_edge(n.nodeinfo["addr"], p["addr"])
            if(p["addr"] not in positions.keys()):
                positions[p["addr"]] = p["loc"]
    except:
        positions[n.nodeinfo["addr"]] = (1.0,1.0)

nx.draw(G, pos=positions, labels={x:x for x in urls})

plt.show()
