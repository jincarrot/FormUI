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
    return s.GetSystem(Namespace, SystemNameServer)

def getClientSystem():
    import mod.client.extraClientApi as c
    return c.GetSystem(Namespace, SystemNameClient)

def getSystem():
    if isServer():
        return getServerSystem()
    else:
        return getClientSystem()
