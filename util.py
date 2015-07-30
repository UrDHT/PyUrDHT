class PeerInfo(object):
    """
        Peerinfo does not actually do much
        I might just reduce it to a 2-tuple

        right now UrDHT is not enforcing a mapping of hashIDs to servers
    """
    def __init__(self,hashID,addr,loc):
        """
            hashID is a string encoded in multihash format
            addr is whatever the network module needs to connect
        """
        self.id = hashID
        self.addr = addr
        self.loc = loc

    def __str__(self):
        return """{"id":"%s", "addr":"%s", "loc":[%f,%f]}"""%(self.id,self.addr,self.loc[0],self.loc[1])

    def __hash__(self):
        return hash((hash(self.id),hash(self.addr)))

    def __eq__(self,other):
        return hash(self)==hash(other)

    def __repr__(self):
        return str(self)
