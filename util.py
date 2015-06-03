class PeerInfo(object):
    """
        Peerinfo does not actually do much
        I might just reduce it to a 2-tuple

        right now UrDHT is not enforcing a mapping of hashIDs to servers
    """
    def __init__(self,hashID,addr):
        """
            hashID is a string encoded in multihash format
            addr is whatever the network module needs to connect
        """
        self.id = hashID
        self.addr = addr

    def __str__(self):
        return """{"id":"%s", "addr":"%s"}"""%(self.id,self.addr)

    def __hash__(self):
        return hash((hash(self.id),hash(self.addr)))

    def __eq__(self,other):
        return hash(self)==hash(other)

    def __repr__(self):
        return str(self)
