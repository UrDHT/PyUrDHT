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
		url = json.loads("""{"id":"3hM7FqFmj1K3U8DWWHd5jv2ufTbz", "addr":"http://127.0.0.1:8080/"}""")
		bootstrap = util.PeerInfo(url["id"],url["addr"])
		print("bootstrap!",bootstrap)
		
	



	path = "http://%s:%d/"%(ip,port)
	hashid = genHash(path,0x11)

	

	peerinfo = util.PeerInfo(hashid,path)

	print(peerinfo)

	if bootstrap is None:
		bootstrap = peerinfo

	logic = LogicClass.DHTLogic(peerinfo)

	net = NetworkClass.Networking(ip,port)

	data = DataBaseClass.DataBase()

	logic.setup(net)
	net.setup(logic,data)

	logic.join(bootstrap)