# -*- coding: utf-8 -*-
import mod.server.extraServerApi as s
from ..config import Namespace, SystemNameClient

ServerSystem = s.GetServerSystemCls()

class Server(ServerSystem):

    def __init__(self, namespace, systemName):
        ServerSystem.__init__(self, namespace, systemName)
        from ..general.managers.observable import ObservableManager
        from ..general.managers.form import FormManager
        from ..general.managers.control import ControlManager
        from ..general.screen import Screen
        self.observableManager = ObservableManager()
        self.formManager = FormManager()
        self.controlManager = ControlManager()
        self.screen = Screen()
        self.listenEvents()

    def listenEvents(self):
        self.ListenForEvent(Namespace, SystemNameClient, "buttonTriggerCallback", self, self.onButtonTrigger)
        self.ListenForEvent(Namespace, SystemNameClient, "applyObservableUpdate", self, self.applyObservableUpdate)
        self.ListenForEvent(Namespace, SystemNameClient, "setDefaultStyle", self, self.setDefaultStyle)
        self.ListenForEvent(Namespace, SystemNameClient, 'requestControls', self, self.onRequestControls)

    def onRequestControls(self, data):
        for registration in self.controlManager.getRegisteredData():
            self.NotifyToClient(data['playerId'], 'registerControl', registration)

    def onButtonTrigger(self, data):
        form = self.formManager.get(data['formId'])
        if form:
            form._btnCallbacks[data['callbackId']](data['playerId'])

    def applyObservableUpdate(self, data):
        self.observableManager.get(data['obId']).setValue(data['value'])

    def setDefaultStyle(self, data):
        self.screen.setDefaultStyle(data['controlType'], data['style'])
