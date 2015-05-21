"""

This file describes the Networking class and associated helper threads/objects
see: https://github.com/UrDHT/DevelopmentPlan/blob/master/Network.md



"""
import server
import myrequests as requests
import json
import util

class Networking(object):
	def __init__(self,ip,port):
		self.serverthread = server.getThread(ip,port)
		self.serverthread.start()

	def setup(self,logic,data):
		server.setlinks(logic,data)

	def seek(self,remote,id):
		path = remote.addr+"api/v0/peer/"+"seek/%s" % id 
		r = requests.get(path)

		
		results = r.json()
		return util.PeerInfo(results["id"],results["addr"])

	def getPeers(self,remote):
		
		r = requests.get(remote.addr+"api/v0/peer/getPeers/")
		#print(r.text)
		#print(r.text)
		#print(r.text)

		result = []
		if len(r.json()) == 0:
			return []
		for p in r.json():
			newpeer = util.PeerInfo(p["id"],p["addr"])
			result.append(newpeer)
		return result

	def notify(self,remote,origin):
		#print("SENDING NOTIFY",remote,origin)
		try:
			r = requests.post(remote.addr+"api/v0/peer/notify", data=str(origin))
			print("The Post Worked")
			return r.status_code == requests.codes.ok
		except:
			print("The Post failed")
			return False

