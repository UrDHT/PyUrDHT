## This is the REST API server. I've tried to make it pretty flexible,
## so it supports both URI path segments and query strings and always returns
## JSON-formatted data. I've separated the URIs into the following format:
# http://server:port/api_version/[client|peer]/[operation]/[data]. Feel
# free to test this by running 'python server.py' and using the Curl
# utility like so: 'curl localhost:8000/apiv01/client/get/test' or whatever.

import cherrypy
from PyUrDHT import NetworkClass

api_version = "apiv01"

class Root(object):
    exposed = True    
    pass

class Client(object):
    exposed = True

    def __init__(self):
        pass

    @cherrypy.tools.json_out()
    def POST(self, *vpath, **params):
        print(vpath)
        return {"error": "Not Supported"}

    @cherrypy.tools.json_out()
    def GET(self, *vpath, **params):
        print(vpath)
        return {"error": "Not Supported"}

class Peer(object):
    exposed = True    
    
    def __init__(self):
        pass

    @cherrypy.tools.json_out()
    def POST(self, *vpath, **params):
        print(vpath)
        return {"error": "Not Supported"}

    @cherrypy.tools.json_out()
    def GET(self, *vpath, **params):
        print(vpath)
        return {"error": "Not Supported"}


class GetValue():
    ''' checks the database of the Node and 
        returns the value if found. '''
    def __init__(self):
        pass

class StoreValue(object):
    ''' reads in posted value and stores it 
        locally at a given id. '''
    def __init__(self):
        pass

class SeekPeer(object):
    ''' Asks the node to provide a peer closer 
        to the given record. '''
    def __init__(self):
        pass

class GetPeers(object):
    ''' Returns a node's list of peers. Useful 
        for join and maintenance. '''
    def __init__(self):
        pass

class Notify(object):
    ''' Post the node information of the sending node.
        Notifies a remote node that a given node exists.
        It is up to the remote node to decide what to do 
        with that information. '''

    def __init__(self):
        pass

def main():
    root = Root()
    root.client = Client()
    root.peer = Peer()
    conf = {
        'global': {
            'server.socket_host': '0.0.0.0',
            'server.socket_port': 8000,
        },
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
        },
    }
    cherrypy.quickstart(root, '/' + api_version + '/', conf)

main()
