from .LogicClass import KADLogic


def setup(pInfo):
    global parentInfo
    global wsAddr
    parentInfo = pInfo
    print("KAD SETUP!", KADLogic)
    return {'LogicClass': KADLogic, 'NetHandler': None} # returns a logic class or None""
