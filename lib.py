import sys
if "./vendored/" not in sys.path:
    sys.path = ["./vendored/"]+sys.path

import NetworkClass
import DataBaseClass
import LogicClass
import util
from pymultihash import genHash

import UrClientPython as Client

import json
import random
import time
import sys
from multiprocessing import Process
if sys.platform == 'win32':
    import multiprocessing.reduction    # make sockets pickable/inheritable

import argparse

from importlib.machinery import SourceFileLoader



import copy

def config_generator(defaults, ports):
    for p in ports:
        d = copy.deepcopy(defaults)
        d["bindPort"] = p
        d["publicAddr"] = "http://%s:%d/" % (d["bindAddr"], p)
        yield d

def fireup_network(ports):
    default = {
	"bindAddr":"127.0.0.1",
	"bindPort":8000,
	"publicAddr":"http://127.0.0.1:8000/",
	"loc":"",
	"services":{}
    }
    bootstraps = []
    output = []
    for config in config_generator(default, ports):
        i = UrDHTInstance(config)
        i.start(bootstraps)
        bootstraps.append(i.nodeinfo)
        output.append(i)
    print("NETWORK LAUNCHED")
    return output



class UrDHTInstance(object):
    def __init__(self, config):
        self.process = None
        self.bootstraps = None
        self.config = config
        self.nodeinfo = {"addr":self.config["publicAddr"], "id": genHash(self.config["publicAddr"],0x12), "loc": (0, 0)}
        self.Client = Client.UrDHTClient("UrDHT", [self.nodeinfo])

    def start(self, bootstraps):
        self.process = Process(target=launch, args=(self.config, bootstraps))
        self.process.start()

    def kill(self):
        self.process.terminate()


def launch(config, bootstraps):

    ip = config["bindAddr"]
    port = config["bindPort"]

    loc = None
    if type(config["loc"]) is type([]) and len(config["loc"]) == 2:
        print("updating loc")
        loc = tuple(config["loc"])

    net = NetworkClass.Networking(ip, port)


    data = DataBaseClass.DataBase()


    peerPool = [util.PeerInfo(x["id"],x["addr"],x["loc"]) for x in bootstraps]
    print(peerPool)

    peerPool = list(filter(lambda x: net.ping("UrDHT",x), peerPool))#filter only living bootstrap peers



    path = config["publicAddr"]
    if len(path) == 0 and len(peerPool) > 0:
        random_peer = random.choice(peerPool)
        pubip = net.getIP("UrDHT",random_peer)
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
    clientPeers = [json.loads(str(myPeerInfo))]
    if len(peerPool) > 0:
        strings = map(str,peerPool)
        clientPeers = json.loads("[%s]"%",".join(strings))
    myClient = Client.UrDHTClient("UrDHT",clientPeers)

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
    while(True):
        time.sleep(1000000)
