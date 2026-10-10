# -*- coding: utf-8 -*-
from ..observable import Observable
from ...utils.environment import isServer, getServerSystem, getClientSystem

class ObservableManager:
    """
    Manager of observables.
    """

    def __init__(self):
        self.__observables = {} # type: dict[int, Observable]
    
    def create(self, value):
        """Create an observable."""
        v = Observable(value)
        self.__observables[v._id] = v
        return v

    def update(self, id, value):
        """Trigger when use Observable.value = x."""
        data = {"id": id, "value": value}
        system = getServerSystem() if isServer() else getClientSystem()
        manager = getattr(system, 'controlManager', None)
        if manager and hasattr(manager, 'applyObservableUpdate'):
            manager.applyObservableUpdate(id, value)
        if isServer():
            server = getServerSystem()
            server.BroadcastToAllClient("applyObservableUpdate", data)
        else:
            client = getClientSystem()
            client.applyObservableUpdate(data)

    def get(self, id):
        return self.__observables[id] if id in self.__observables else None

