"""
This file describes the Networking class and associated helper threads/objects
see: https://github.com/UrDHT/DevelopmentPlan/blob/master/Network.md
"""
import server
import myrequests as requests
import util


class DialFailed(Exception):
    pass


class Networking(object):

    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.handlers = {}
        self.netHandlers = {}

    def setup(self, logic, data):
        """
        Lets the server know which LogicClass and DataClass to use
        """

        self.serverThread = server.getThread(self.ip, self.port)
        self.serverThread.start()
        self.handlers["UrDHT"] = logic
        self.netHandlers["UrDHT"] = None
        server.setLinks(self.handlers, self.netHandlers, data)

    def addHandler(self, key, logic, netHandler):
        self.handlers[key] = logic
        self.netHandlers[key] = netHandler

    def seek(self, service, remote, id):
        """
        This function remotely calls seek on the remote node,
        asking it to run LogicComponent.seek() on id
        """
        path = remote.addr + service + "/peer/" + "seek/%s" % id
        val = None
        try:
            r = requests.get(path)
            results = r.json()
            val = util.PeerInfo(results["id"], results["addr"], results["loc"])
        except Exception:
            raise DialFailed()
        return val

    def seekPoint():
        pass


    def removeThisNode():
        pass

    def getPeers(self, service, remote):
        result = []
        try:
            r = requests.get(remote.addr + service + "/peer/getPeers/")
            # print(r.text)
            # print(r.text)
            # print(r.text)
            if len(r.json()) == 0:
                return []
            for p in r.json():
                newPeer = util.PeerInfo(p["id"], p["addr"], p["loc"])
                result.append(newPeer)
        except Exception:
            raise DialFailed()
        return result

    def getSuccessors(self, service, remote):
        result = []
        try:
            r = requests.get(remote.addr + service + "/peer/getSuccessors/")
            if len(r.json()) == 0:
                return []
            for p in r.json():
                newPeer = util.PeerInfo(p["id"], p["addr"], p["loc"])
                result.append(newPeer)
        except Exception:
            raise DialFailed()
        return result

    def getPredecessor(self, service, remote):
        result = []
        try:
            r = requests.get(remote.addr + service + "/peer/getPredecessor/")
            if len(r.json()) == 0:
                return []
            for p in r.json():
                newPeer = util.PeerInfo(p["id"], p["addr"], p["loc"])
                result.append(newPeer)
        except Exception:
            raise DialFailed()
        return result

    def notify(self, service, remote, origin):
        # print("SENDING NOTIFY",remote,origin)
        try:
            r = requests.post(remote.addr + service + "/peer/notify", data=str(origin))
            return r.status_code == requests.codes.ok
        except:
            return False

    def store(self, service, remote, id, data):
        # print("SENDING NOTIFY",remote,origin)
        try:
            r = requests.post(remote.addr + service + "/client/store/" + id, data=data)
            return r.status_code == requests.codes.ok
        except:
            return False

    def getIP(self, service, remote):
        ip = None
        try:
            r = requests.get(remote.addr + service + "/peer/getmyIP")
            ip = r.text
        except:
            raise DialFailed()
        return ip

    def ping(self, service, remote):
        try:
            r = requests.get(remote.addr + service + "/peer/ping")

            return r.status_code == requests.codes.ok
        except:
            return False
