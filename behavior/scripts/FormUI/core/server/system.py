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
        self.observableManager = ObservableManager()
        self.formManager = FormManager()
        self.controlManager = ControlManager()
        self.listenEvents()

    def listenEvents(self):
        self.ListenForEvent(Namespace, SystemNameClient, "registerControl", self, self.registerControl)
        self.ListenForEvent(Namespace, SystemNameClient, "buttonTriggerCallback", self, self.onButtonTrigger)
        self.ListenForEvent(s.GetEngineNamespace(), s.GetEngineSystemName(), "LoadServerAddonScriptsAfter", self, self.initInnerControls)

    def initInnerControls(self, data):
        from ..general.controls.oreui import OreUI
        OreUI()

    def registerControl(self, data):
        self.controlManager.create(data['type'], data['name'], data['path'], data['options'])

    def onButtonTrigger(self, data):
        form = self.formManager.get(data['formId'])
        if form:
            form._btnCallbacks[data['callbackId']]()

        