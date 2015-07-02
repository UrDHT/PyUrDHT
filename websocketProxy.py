#!/usr/bin/env python

"""

{
	
	method:"seek",
	id:"optional, post cmd text /seek/{id}
	args:{more json}

}



"""
def main(wsBindAddr,wsBindPort,hostPath):
	import asyncio
	import websockets
	import json
	import myrequests as requests

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
	    	output = r.text
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

