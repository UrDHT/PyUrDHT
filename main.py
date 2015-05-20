import NetworkClass
import DataBaseClass
import LogicClass
import util
from pymultihash import genHash

ip = "127.0.0.1"
port = 8080

path = "http://%s:%d/"%(ip,port)
hashid = genHash("sha1",0x11)

print(hashid)

peerinfo = util.PeerInfo(hashid,path)


logic = LogicClass.DHTLogic(peerinfo)

net = NetworkClass.Networking(ip,port)

data = DataBaseClass.DataBase()

logic.setup(net)
net.setup(logic,data)

logic.join(peerinfo)