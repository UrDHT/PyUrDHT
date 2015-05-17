"""

This file describes the DHT Logic class and associated helper threads/objects
see: https://github.com/UrDHT/DevelopmentPlan/blob/master/DHT_Logic.md


"""

"""
# DHT Logic Module

This module is the most complex and is close to being a god object for the project.
Most refinement and modifications required for re-purposing will happen here.

The DHT Logic exposes:

- seek(id) -> return a good forward peer for an id
- getPeers() -> return my current list of 1 hop peers
- getNotified(origin) -> notify me that origin exists
- DoIOwn(id) -> returns True iff I think I am responsible for an address.

The DHT Logic Depends On:

- Network Component: Allows communication with other nodes
    - Seek(remote,id) 
    - GetPeers(remote)
    - Notify(remote,origin)


DHT logic can be internally separated into two parts:
    - Reactive Logic:
        - dealing with queries
        - Has a dedicated worker, processes requests as fast as possible
    - Periodic Logic:
        - deals with maintenance
        - essentially an infinite loop with sleeps.

# TODO:
    - Decide on a good method for dealing with bad peers!!!!!

## Reactive Logic:
 Dealing with a reactive query should work as follows:
 ```
    get read lock on peerinfo
    copy needed peerinfo into local memory
    release read lock on peerinfo
    do required computation generally just a "findmax"
    return value
```

## Periodic Logic:
```
    do while running:
        get read lock on peerinfo
        make local copy
        release read lock on peerinfo
        notify all peers
        sleep for a bit
        get read lock on new_canidates
        make a local copy
        release read lock on new_canidates
        new_peerlist = pick_new_peerlist(peerinfo_copy + new_canidates_copy)
        get write lock on peerinfo
        write new_peerlist over peerinfo
        release write lock on peerinfo
        sleep for a bit

```

"""


class DHTLogic(object):
    def __init__(self):
        pass
    def setup(self, network):
        pass
    def shutdown(self):
        pass
    def seek(self,id):
        pass
    def getPeers(self):
        pass
    def getNotified(self,origin):
        pass
    def DoIOwn(self,id):
        pass

