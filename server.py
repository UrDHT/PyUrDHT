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
        s.send_header("Content-type", "application/json")
        s.end_headers()
    def do_GET(self):
        self.do_HEAD()
        #self.wfile.write(b"HTTP/1.1 200 OK\n")
        if None != re.search('/api/v0/client/seek/*', self.path):
            recordID = self.path.split('/')[-1]
            result = mylogic.seek(recordID)
            answer = bytes(str(result),"UTF-8")
            self.wfile.write(answer)
        if None != re.search('/api/v0/peer/seek/*', self.path):
            recordID = self.path.split('/')[-1]
            result = mylogic.seek(recordID)
            answer = bytes(str(result),"UTF-8")
            self.wfile.write(answer)
        if None != re.search('/api/v0/client/get/*', self.path):
            recordID = self.path.split('/')[-1]
            result = myDB.get(recordID)
            answer = bytes(json.dumps(result))
            self.wfile.write(answer)
        if None != re.search('/api/v0/peer/getPeers*', self.path):
            recordID = self.path.split('/')[-1]
            result_list = mylogic.getPeers()
            result = map(str,result_list)
            answer = "[%s]"%",".join(result)
            self.wfile.write(bytes(answer,"UTF-8"))



    def do_POST(self):
        self.do_HEAD()
        #self.wfile.write(b"HTTP/1.1 200 OK\n")
        if None != re.search('/api/v0/client/store/*', self.path):
            content_len = int(self.headers.get_all('content-length')[0])
            data = self.rfile.read(content_len)
            recordID = self.path.split('/')[-1]
            myDB.store(recordID,data)

        elif None != re.search('/api/v0/peer/notify*', self.path):
            print(self.path)

            content_len = int(self.headers.get_all('content-length')[0])
            data = self.rfile.read(content_len)
            #data = self.rfile.read()
            print("NOTIFIED",data)
            json_dict = json.loads(str(data,"UTF-8"))
            addr = json_dict["addr"]
            hashid = json_dict["id"]
            mylogic.getNotified(PeerInfo(hashid,addr))
            self.wfile.write(b"[]")

def getThread(ip='0.0.0.0',port=8000):
    server = http.server.HTTPServer((ip,port), RESTHandler)
    return threading.Thread(target=server.serve_forever)
