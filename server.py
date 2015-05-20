## This is the REST API server. I've tried to make it pretty flexible,
## so it supports both URI path segments and query strings and always returns
## JSON-formatted data. I've separated the URIs into the following format:
# http://server:port/api_version/[client|peer]/[operation]/[data]. Feel
# free to test this by running 'python server.py' and using the Curl
# utility like so: 'curl localhost:8000/apiv01/client/get/test' or whatever.

import threading

from util import PeerInfo

import http.server
import json
import re, cgi

api_version = "api/v0"

mylogic = None
myDB = None

def setlinks(logic,db):
	global mylogic
	global myDB
	mylogic = logic
	myDB = db

class RESTHandler(http.server.BaseHTTPRequestHandler):
	def do_HEAD(s):
		s.send_response(200)
		s.send_header("Content-type", "text/json")
		s.end_headers()
	def do_GET(s):
		pass

	def do_POST(s):
		if None != re.search('/api/v0/client/store/*', self.path):
			ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
			if ctype == 'application/json':
				length = int(self.headers.getheader('content-length'))
				data = cgi.parse_qs(self.rfile.read(length), keep_blank_values=1)
				recordID = self.path.split('/')[-1]
				myDB.store(recordID,data)

		if None != re.search('/api/v0/peer/notify', self.path):
			ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
			if ctype == 'application/json':
				length = int(self.headers.getheader('content-length'))
				data = cgi.parse_qs(self.rfile.read(length), keep_blank_values=1)
				json_dict = json.loads(data)
				addr = json_dict["addr"]
				hashid = json_dict["id"]
				mylogic.getNotified(PeerInfo(hashid,addr))

def getThread(ip='0.0.0.0',port=8000):
	server = http.server.HTTPServer((ip,port), RESTHandler)
	return threading.Thread(target=server.serve_forever)
