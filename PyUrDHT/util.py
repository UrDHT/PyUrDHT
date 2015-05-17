class PeerInfo(object):
    """
        Peerinfo does not actually do much
        I might just reduce it to a 2-tuple

        right now UrDHT is not enforcing a mapping of hashids to servers
    """
    def __init__(self,hashid,addr):
        """
            hashid is a byte string
            addr is whatever the network module needs to connect
        """
        self.id = hashid
        self.addr = addr

