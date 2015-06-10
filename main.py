import NetworkClass
import DataBaseClass
import LogicClass
import util
from pymultihash import genHash

import json
import random


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

	wsip = config["wsBindAddr"]
	wsport = config["wsBindPort"]
	wsPath = config["wsAddr"]

	net = NetworkClass.Networking(ip,port)


	data = DataBaseClass.DataBase()


	bootstraps = jsonLoad(config["bootstraps"])
	
	peerPool = [util.PeerInfo(x["id"],x["addr"],x["wsAddr"]) for x in bootstraps]

	peerPool = list(filter(lambda x: net.ping(x), peerPool))#filter only living bootstrap peers


	path = config["publicAddr"]
	if len(path) == 0 and len(peers) > 0:
		random_peer = random.choice(peerPool)
		pubip = net.getIP(random_peer)
		path = "http://%s:%d" % (pubip, port)

	hashid = genHash(path,0x11)

	
	myPeerInfo = util.PeerInfo(hashid,path, wsPath)

	
	logic = LogicClass.DHTLogic(myPeerInfo)

	net.setup(logic,data)

	logic.setup(net)
	

	logic.join(peerPool)

	print("Node up and Running")
	print(myPeerInfo)
