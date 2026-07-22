# -*- coding: utf-8 -*-
from ..observable import Observable
from ...utils.environment import isServer, getServerSystem, getClientSystem

class ObservableManager:
    """
    Manager of observables.
    """

    def __init__(self):
        self.__observables = {} # type: dict[int, Observable]
        self.__currentId = 1 if isServer() else -1
    
    def create(self, value):
        """Create an observable."""
        v = Observable(value, self.__currentId)
        self.__observables[self.__currentId] = v
        self.__currentId += 1 if isServer() else -1
        return v

    def update(self, id, value):
        """Trigger when use Observable.value = x."""
        data = {"id": id, "value": value}
        if isServer():
            server = getServerSystem()
            server.BroadcastToAllClient("applyObservableUpdate", data)
        else:
            client = getClientSystem()
            client.applyObservableUpdate(data)

