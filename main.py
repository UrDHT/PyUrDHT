import NetworkClass
import DataBaseClass
import LogicClass
import util
from pymultihash import genHash

import json
import random, time
import sys
import websocketProxy
from multiprocessing import Process
if sys.platform == 'win32':
    import multiprocessing.reduction    # make sockets pickable/inheritable



import argparse

def jsonLoad(fname):
    with open(fname,"r") as fp:
        return json.load(fp)


if __name__=="__main__":


    parser = argparse.ArgumentParser()
    parser.add_argument("--config",default="./config.json",help="Use a specific configuration file")
    args = parser.parse_args()

    configpath = "./config.json"
    if args.config:
        configpath = args.config
    config = jsonLoad(configpath)


    ip = config["bindAddr"]
    port = config["bindPort"]

    loc = None
    if type(config["loc"]) is type([]) and len(config["loc"]) == 2:
        print("updating loc")
        loc = tuple(config["loc"])

    net = NetworkClass.Networking(ip,port)


    data = DataBaseClass.DataBase()


    bootstraps = jsonLoad(config["bootstraps"])


    peerPool = [util.PeerInfo(x["id"],x["addr"],x["loc"]) for x in bootstraps]
    print(peerPool)

    peerPool = list(filter(lambda x: net.ping("UrDHT",x), peerPool))#filter only living bootstrap peers



    path = config["publicAddr"]
    if len(path) == 0 and len(peerPool) > 0:
        random_peer = random.choice(peerPool)
        pubip = net.getIP(random_peer)
        path = "http://%s:%d/" % (pubip, port)
    else:
        if path[-1] != "/":
            path += "/"
        if path[0:4] != "http":
            path = "http://"+ path


    hashid = genHash(path,0x12)


    myPeerInfo = util.PeerInfo(hashid,path, loc)


    logic = LogicClass.DHTLogic(myPeerInfo,"UrDHT")

    net.setup(logic,data)

    logic.setup(net,data)


    logic.join(peerPool)

    print("Node up and Running")
    print(logic.info)
