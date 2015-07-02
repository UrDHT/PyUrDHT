import NetworkClass
import DataBaseClass
import LogicClass
import util
import logging
import errors as error
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

	logger = logging.getLogger(__name__)

	parser = argparse.ArgumentParser()
	parser.add_argument("--config",default="./config.json",help="Use a specific configuration file")
	parser.add_argument("-d","--debug",help="Turn on debugging output",type=int)
	args = parser.parse_args()

	configpath = "./config.json"
	if args.config:
		configpath = args.config
	config = jsonLoad(configpath)

	if args.debug:
		error.debugging = True
		error.debugLevel = args.debug
		#logger.setLevel(args.debug*10)

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
		path = "http://%s:%d/" % (pubip, port)

	hashid = genHash(path,0x12)


	myPeerInfo = util.PeerInfo(hashid,path, wsPath)


	logic = LogicClass.DHTLogic(myPeerInfo)

	net.setup(logic,data)

	logic.setup(net,data)


	logic.join(peerPool)

	logger.info("Node up and Running")
	logger.debug(str(myPeerInfo))

	p = Process(target=websocketProxy.main, args=(wsip, wsport, path+"/api/v0/client/"),daemon=True)
	p.start()

	logger.info("started websocket proxy")
