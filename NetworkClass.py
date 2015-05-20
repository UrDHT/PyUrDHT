"""

This file describes the Networking class and associated helper threads/objects
see: https://github.com/UrDHT/DevelopmentPlan/blob/master/Network.md



"""
import server
import requests
import json

class Networking(object):
	def __init__(self,ip,port):
		self.serverthread = server.getThread(ip,port)
		self.serverthread.start()

	def setup(self,logic,data):
		server.setlinks(logic,data)

	def seek(self,remote,id):
		
		r = requests.get(remote.addr+"api/v0/peer/"+"seek/%s" % id )
		return json.loads(r.json())

	def getPeers(self,remote):
		
		r = requests.get(remote.addr+"api/v0/getpeers/")
		return json.loads(r.json())

	def notify(self,remote,origin):

		r = request.post(remote.addr+"api/v0/notify", params=origin)
		return json.loads(r.json())

