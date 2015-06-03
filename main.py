import NetworkClass
import DataBaseClass
import LogicClass
import util
from pymultihash import genHash
import sys
import json

if __name__=="__main__":
	ip = "127.0.0.1"
	port = 8080
	bootstrap = None
	if len(sys.argv)>1:
		url = sys.argv[1].split(":")
		ip = url[0]
		port = int(url[1])
	if len(sys.argv)>2:
		url = json.loads("""{"id":"31V1kNSUfDXD7eZKtd7MWuHFUUyo", "addr":"http://45.79.205.125:8000/"}""")
		bootstrap = util.PeerInfo(url["id"],url["addr"])
		print("bootstrap!",bootstrap)
		
	



	path = "http://%s:%d/"%(ip,port)
	hashID = genHash(path,0x11)

	

	peerInfo = util.PeerInfo(hashID,path)

	print(peerInfo)

	if bootstrap is None:
		bootstrap = peerInfo

	logic = LogicClass.DHTLogic(peerInfo)

	net = NetworkClass.Networking("0.0.0.0",port)

	data = DataBaseClass.DataBase()

	logic.setup(net)
	net.setup(logic,data)

	logic.join(bootstrap)
