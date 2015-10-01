from .LogicClass import KADLogic


def setup(pInfo):
    global parentInfo
    global wsAddr
    parentInfo = pInfo
    return {'LogicClass': KADLogic, 'NetHandler': None} # returns a logic class or None""
