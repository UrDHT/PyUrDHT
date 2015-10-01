#!/usr/bin/env python

"""

{

    method:"seek",
    id:"optional, post cmd text /seek/{id}
    args:{more json}

}



"""

import re

parentInfo = None
wsAddr = None

def setup(pInfo):
    global parentInfo
    global wsAddr
    parentInfo = pInfo
    addr = pInfo.addr.split(":")[1][2:]
    wsAddr = "ws://%s:8023"%addr
    #turned back on #turned off for testing. have more than 1 borks things
    from multiprocessing import Process
    p = Process(target=threadTarget,args=["0.0.0.0",8023,pInfo.addr+"websocket/client/"])
    p.start();

    return {'LogicClass':None,'NetHandler':MyHandler} # returns a logic class or None""

def MyHandler(self):
    if None != re.search('websocket/client/wsinfo*', self.path):
        self.success()
        self.wfile.write(bytes(wsAddr,"UTF-8"))
        return True
    else:
        self.failure()
        return False


def threadTarget(wsBindAddr,wsBindPort,hostPath):
    import asyncio
    from . import websockets
    import json
    from . import myrequests as requests

    def wsResolve(path):
        newpath = ''.join((path,"websocket/client/wsinfo"))
        print(newpath)
        r = requests.get(newpath)
        return r.text

    @asyncio.coroutine
    def proxy(websocket, path):
        cmd_text = yield from websocket.recv()
        print(cmd_text)
        cmd = json.loads(cmd_text)
        output = ""
        if cmd["method"] == "seek":
            seekarg = cmd["id"]
            newpath = ''.join((hostPath,"seek/",seekarg))
            r = requests.get(newpath)
            peer = r.json()
            peerAddr = peer["addr"]
            wsaddr = wsResolve(peerAddr)
            peer["wsAddr"] = wsaddr
            print(json.dumps(peer))
            output = json.dumps(peer)
        if cmd["method"] == "get":
            seekarg = cmd["id"]
            newpath = ''.join((hostPath,"get/",seekarg))
            r = requests.get(newpath)
            output = r.text
        if cmd["method"] == "poll":
            seekarg = cmd["id"]
            t = cmd["time"]
            newpath = ''.join((hostPath,"poll/",seekarg,"/",str(t)))
            r = requests.get(newpath)
            output = r.text
        if cmd["method"] == "store":
            seekarg = cmd["id"]
            newpath = ''.join((hostPath,"store/",seekarg))
            data = json.dumps(cmd["data"])
            r = requests.post(newpath, data=data)
            output = r.text
        if cmd["method"] == "post":
            seekarg = cmd["id"]
            newpath = ''.join((hostPath,"post/",seekarg))
            data = json.dumps(cmd["data"])
            r = requests.post(newpath, data=data)
            output = r.text

        yield from websocket.send(output)

    start_server = websockets.serve(proxy, wsBindAddr, wsBindPort)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
