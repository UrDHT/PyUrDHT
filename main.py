import sys
if "./vendored/" not in sys.path:
    sys.path = ["./vendored/"]+sys.path

import NetworkClass
import DataBaseClass
import LogicClass
import util


from pymultihash import genHash

import json
import random, time
import sys
from multiprocessing import Process
if sys.platform == 'win32':
    import multiprocessing.reduction    # make sockets pickable/inheritable



import argparse
from importlib.machinery import SourceFileLoader

import UrClientPython3 as client

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
        pubip = net.getIP("UrDHT",random_peer)
        path = "http://%s:%d/" % (pubip, port)
    elif len(path) != 0:#make sure there is a path
        if path[-1] != "/":
            path += "/"
        if path[0:7] != "http://":#need to remeber this if we add more protocols
            path = "http://"+ path
    else:
        print("""
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
You have left the publicAddr property in config.json empty and there are no
bootstraps to discover your external IP address for you.
You either:
    - Did not provide bootstraps
    - Cannot connect to any bootstraps (either they are offline or you are)

To fix this:
    - Figure out your external IP and provide it in config.json
    - If you are testing, you can use localhost as your ip
    - Make sure your internet is working
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
""")
        sys.exit()


    hashid = genHash(path,0x12)


    myPeerInfo = util.PeerInfo(hashid,path, loc)


    logic = LogicClass.DHTLogic(myPeerInfo,"UrDHT")

    net.setup(logic,data)

    logic.setup(net,data)
    clientPeers = [json.loads(str(myPeerInfo))]
    if len(peerPool) > 0:
        strings = map(str,peerPool)
        clientPeers = json.loads("[%s]"%",".join(strings))
    myClient = client.UrDHTClient("UrDHT",clientPeers)

    logic.join(peerPool)

    print("Node up and Running")
    print(logic.info)

    service_ids = config["services"]
    services = {}
    #time.sleep(5)
    for k in service_ids.keys():
        serviceInfo = None
        command = """
import %s as foo
serviceInfo = foo.setup(myPeerInfo)
""" % ("services."+service_ids[k])
        exec(command)
        myLogicClass = serviceInfo['LogicClass']
        if(myLogicClass is None):
            print("Loading default logic class)")
            myLogicClass = LogicClass.DHTLogic

        services[k] = myLogicClass(myPeerInfo,k)
        net.addHandler(k,services[k],serviceInfo['NetHandler'])
        services[k].setup(net,data)
        subnetPeerPool = [myPeerInfo]
        try:
            c = json.loads(myClient.get(k))
            print(c)
            if len(c) == 0:
                raise Exception()
            subnetPeerPool = [util.PeerInfo(x["id"],x["addr"],x["loc"]) for x in c]
        except:
            print("Peer discovery for %s failed. May be only peer in subnet" % k)
        services[k].join(subnetPeerPool)
        #print(subnetPeerPool)
        old_list = myClient.get(k)
        new_list = []
        if(old_list):
            new_list = json.loads(old_list)
        new_list.append(json.loads(str(myPeerInfo)))
        myClient.store(k,json.dumps(new_list))
