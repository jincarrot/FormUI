# -*- coding: utf-8 -*-
from ..config import Namespace, SystemNameServer, SystemNameClient

def isServer():
    """Returns true if the code is running in server."""
    try:
        import mod.client.extraClientApi as clientApi
        return clientApi.GetLocalPlayerId() == "-1"
    except:
        return True
    
def isClient():
    """Returns true if the code is running in client."""
    return not isServer()

def getServerSystem():
    import mod.server.extraServerApi as s
    system = s.GetSystem(Namespace, SystemNameServer)
    if not system:
        from ..init_system import server_system_path
    return system

def getClientSystem():
    import mod.client.extraClientApi as c
    system = c.GetSystem(Namespace, SystemNameClient)
    if not system:
        from ...register import client_system_path
    return system

def getSystem():
    if isServer():
        return getServerSystem()
    else:
        return getClientSystem()

def requestDataFromOtherSide(dataId):
    data = yield
