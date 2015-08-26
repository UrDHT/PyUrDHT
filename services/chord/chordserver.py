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


myHandlers = None
myNetHandlers = None
myDB = None

def setLinks(handlers,netHandlers,db):
    global myHandlers
    global myNetHandlers
    global myDB
    myHandlers = handlers
    myDB = db
    myNetHandlers = netHandlers
    print("LINKS ARE SET")

class RESTHandler(http.server.BaseHTTPRequestHandler):
    def success(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
    def failure(self):
        self.send_response(400)
        self.send_header("Content-type", "application/json")
        self.end_headers()
    def do_HEAD(self):
        """Reply with OK and send headers"""
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

    def do_GET(self):
        """
        Holy boilerplate, Batman!
        """
        k = self.path.split('/')[1]
        if k in myHandlers.keys():
            myLogic = myHandlers[k]

            #self.wfile.write(b"HTTP/1.1 200 OK\n")
            if None != re.search(k+'/client/seek/*', self.path):
                self.success()
                recordID = self.path.split('/')[-1]
                result = myLogic.seek(recordID)
                answer = bytes(str(result),"UTF-8")
                self.wfile.write(answer)
            elif None != re.search(k+'/peer/seek/*', self.path):
                self.success()
                recordID = self.path.split('/')[-1]
                result = myLogic.seek(recordID)
                answer = bytes(str(result),"UTF-8")
                self.wfile.write(answer)
            elif None != re.search(k+'/client/get/*', self.path):
                self.success()
                recordID = self.path.split('/')[-1]
                result = myDB.get(recordID)
                if result:
                    answer = bytes(result)
                    self.wfile.write(answer)

            elif None != re.search(k+'/client/poll/*/*', self.path):
                self.success()
                recordID = self.path.split('/')[-2]
                t = float(self.path.split('/')[-1])
                result = json.dumps(myDB.poll(recordID,t))
                if result:
                    answer = bytes(result,"UTF-8")
                    self.wfile.write(answer)

            elif None != re.search(k+'/peer/getPeers*', self.path):
                self.success()
                recordID = self.path.split('/')[-1]
                result_list = myLogic.getPeers()
                result = map(str,result_list)
                answer = "[%s]"%",".join(result)
                self.wfile.write(bytes(answer,"UTF-8"))

            elif None != re.search(k+'/peer/getSuccessors*', self.path):
                self.success()
                recordID = self.path.split('/')[-1]
                result_list = myLogic.getSuccessors()
                result = map(str,result_list)
                answer = "[%s]"%",".join(result)
                self.wfile.write(bytes(answer,"UTF-8"))

            elif None != re.search(k+'/peer/getPredecessor*', self.path):
                self.success()
                recordID = self.path.split('/')[-1]
                result_list = myLogic.getPredecessor()
                result = map(str,result_list)
                answer = "[%s]"%",".join(result)
                self.wfile.write(bytes(answer,"UTF-8"))

            elif None != re.search(k+'/peer/getmyIP*', self.path):
                self.success()
                self.wfile.write(bytes(self.client_address[0],"UTF-8"))

            elif None != re.search(k+'/peer/ping*', self.path):
                self.success()
                self.wfile.write(b'\"PONG\"')

            elif None != re.search(k+'/peer/info*', self.path):
                self.success()
                self.wfile.write(bytes(str(myLogic.info),"UTF-8"))
            else:
                if myNetHandlers[k] is not None:
                    myNetHandlers[k](self)
                else:
                    self.failure()


    def do_POST(self):
        k = self.path.split('/')[1]
        if k in myHandlers.keys():
            myLogic = myHandlers[k]
            #self.wfile.write(b"HTTP/1.1 200 OK\n")
            if None != re.search(k+'/client/store/*', self.path):
                self.success()
                contentLen = int(self.headers.get_all('content-length')[0])
                data = self.rfile.read(contentLen)
                recordID = self.path.split('/')[-1]
                myDB.store(recordID,data)

            elif None != re.search(k+'/client/post/*', self.path):
                self.success()
                contentLen = int(self.headers.get_all('content-length')[0])
                data = self.rfile.read(contentLen)
                recordID = self.path.split('/')[-1]
                myDB.post(recordID,str(data,"UTF-8"))

            elif None != re.search(k+'/peer/notify*', self.path):
                self.success()
                #print(self.path)

                contentLen = int(self.headers.get_all('content-length')[0])
                data = self.rfile.read(contentLen)
                #data = self.rfile.read()
                #print("NOTIFIED",data)
                jsonDict = json.loads(str(data,"UTF-8"))
                addr = jsonDict["addr"]
                hashID = jsonDict["id"]
                loc = jsonDict["loc"]
                myLogic.getNotified(PeerInfo(hashID,addr,loc))
                self.wfile.write(b"[]")
            else:
                self.failure()
    def log_message(self, format, *args):
        return

def getThread(ip='0.0.0.0',port=8000):
    server = http.server.HTTPServer((ip,port), RESTHandler)
    return threading.Thread(target=server.serve_forever)
