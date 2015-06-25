from . import myrequests as requests
from . import pymultihash as pmh
import time
import random

def dial(target, cmd, **kwargs):

	buildURL = [target["addr"]]
	buildURL.append("api/v0/client/")
	buildURL.append(cmd)
	buildURL.append("/")
	postData = None
	if cmd == "seek" or cmd == "get":
		buildURL.append(kwargs["id"])
	elif cmd == "poll":
		buildURL.append(kwargs["id"])
		buildURL.append("/")
		buildURL.append(str(kwargs["time"]))
	elif cmd == "post":
		buildURL.append(kwargs["id"])
		postData = kwargs["data"]
	elif cmd == "store":
		buildURL.append(kwargs["id"])
		postData = kwargs["data"]

	trgAddr = ''.join(buildURL)
	if postData is not None:
		r = requests.post(trgAddr, data=postData)
		if r.text:
			return r.json()
	else:
		r = requests.get(trgAddr)
		print([x for x in r.text])
		if len(r.text)>0:
			return r.json()		

class UrDHTClient(object):
	def __init__(self, apiStr, bootstraps):
		self.apiStr = apiStr
		self.knownPeers = bootstraps

	def hash(self, string):
		return pmh.genHash(self.apiStr+string,0x12)

	def lookup(self,targetID):
		serverStack = self.knownPeers[:]#I think this is kinda elegant.
		#it will try all the known peers before failing
		random.shuffle(serverStack)
		nextHop = None
		while(not nextHop or nextHop["id"]!=serverStack[-1]["id"]):
			try:
				nextHop = dial(serverStack[-1],"seek",id=targetID)
			except:
				print(serverStack.pop(),"failed dial")

			if len(serverStack) == 0:
				raise Exception("lookup failed")
		return nextHop

	def get(self,key):
		target_id = self.hash(key)
		target_peer = self.lookup(target_id)
		result = dial(target_peer,"get",id=target_id)
		return result

	def store(self,key, data):
		target_id = self.hash(key)
		target_peer = self.lookup(target_id)
		dial(target_peer,"store",id=target_id,data=data)

	def post(self,key, data):
		target_id = self.hash(key)
		target_peer = self.lookup(target_id)
		dial(target_peer,"post",id=target_id,data=data)

	def poll(self,key, time):
		target_id = self.hash(key)
		target_peer = self.lookup(target_id)
		return dial(target_peer,"poll",id=target_id,time=time)


