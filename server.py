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

myLogic = None
myDB = None

def setLinks(logic,db):
    global myLogic
    global myDB
    myLogic = logic
    myDB = db

class RESTHandler(http.server.BaseHTTPRequestHandler):
    def do_HEAD(self):
        """Reply with OK and send headers"""
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

    def do_GET(self):
        """
        Holy boilerplate, Batman!
        """

        self.do_HEAD()
        #self.wfile.write(b"HTTP/1.1 200 OK\n")
        if None != re.search('/api/v0/client/seek/*', self.path):
            recordID = self.path.split('/')[-1]
            result = myLogic.seek(recordID)
            answer = bytes(str(result),"UTF-8")
            self.wfile.write(answer)
        if None != re.search('/api/v0/peer/seek/*', self.path):
            recordID = self.path.split('/')[-1]
            result = myLogic.seek(recordID)
            answer = bytes(str(result),"UTF-8")
            self.wfile.write(answer)
        if None != re.search('/api/v0/client/get/*', self.path):
            recordID = self.path.split('/')[-1]
            result = myDB.get(recordID)
            if result:
                answer = bytes(result)
                self.wfile.write(answer)

        if None != re.search('/api/v0/client/poll/*/*', self.path):
            recordID = self.path.split('/')[-2]
            t = float(self.path.split('/')[-1])
            result = myDB.poll(recordID,t)
            if result:
                answer = bytes(result)
                self.wfile.write(answer)

        if None != re.search('/api/v0/peer/getPeers*', self.path):
            recordID = self.path.split('/')[-1]
            result_list = myLogic.getPeers()
            result = map(str,result_list)
            answer = "[%s]"%",".join(result)
            self.wfile.write(bytes(answer,"UTF-8"))

        if None != re.search('/api/v0/peer/getmyIP*', self.path):
            self.wfile.write(bytes(self.client_address[0],"UTF-8"))

        if None != re.search('/api/v0/peer/ping*', self.path):
            self.wfile.write(b'\"PONG\"')


    def do_POST(self):
        self.do_HEAD()
        #self.wfile.write(b"HTTP/1.1 200 OK\n")
        if None != re.search('/api/v0/client/store/*', self.path):
            contentLen = int(self.headers.get_all('content-length')[0])
            data = self.rfile.read(contentLen)
            recordID = self.path.split('/')[-1]
            myDB.store(recordID,data)

        if None != re.search('/api/v0/client/post/*', self.path):
            contentLen = int(self.headers.get_all('content-length')[0])
            data = self.rfile.read(contentLen)
            recordID = self.path.split('/')[-1]
            myDB.post(recordID,data)

        elif None != re.search('/api/v0/peer/notify*', self.path):
            #print(self.path)

            contentLen = int(self.headers.get_all('content-length')[0])
            data = self.rfile.read(contentLen)
            #data = self.rfile.read()
            #print("NOTIFIED",data)
            jsonDict = json.loads(str(data,"UTF-8"))
            addr = jsonDict["addr"]
            hashID = jsonDict["id"]
            wsAddr = jsonDict["wsAddr"]
            myLogic.getNotified(PeerInfo(hashID,addr,wsAddr))
            self.wfile.write(b"[]")

def getThread(ip='0.0.0.0',port=8000):
    server = http.server.HTTPServer((ip,port), RESTHandler)
    return threading.Thread(target=server.serve_forever)
