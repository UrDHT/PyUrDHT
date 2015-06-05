import NetworkClass
import DataBaseClass
import LogicClass
import util
from pymultihash import genHash
import sys
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
	print(config)

	ip = config["bindAddr"]
	port = config["bindPort"]

	net = NetworkClass.Networking(ip,port)


	data = DataBaseClass.DataBase()


	bootstraps = jsonLoad(config["bootstraps"])
	
	peerPool = [util.PeerInfo(x["id"],x["addr"]) for x in bootstraps]

	peerPool = filter(lambda x: net.ping(x), peerPool)#filter only living bootstrap peers


	path = config["publicAddr"]
	if len(path) == 0 and len(peers) > 0:
		random_peer = random.choice(peerPool)
		pubip = net.getIP(random_peer)
		path = "http://%s:%d" % (pubip, port)

	hashid = genHash(path,0x11)

	
	myPeerInfo = util.PeerInfo(hashid,path)

	
	logic = LogicClass.DHTLogic(myPeerInfo)

	logic.setup(net)
	net.setup(logic,data)

	logic.join(peerPool)
