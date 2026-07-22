# -*- coding: utf-8 -*-
import mod.client.extraClientApi as c
from ..config import Namespace, SystemNameServer
from ..utils.ui import isFormScreen

ClientSystem = c.GetClientSystemCls()

class Client(ClientSystem):

    def __init__(self, namespace, systemName):
        ClientSystem.__init__(self, namespace, systemName)
        from ..general.managers.observable import ObservableManager
        from ..general.managers.form import FormManager
        from ..general.managers.control import ControlManager
        self.observableManager = ObservableManager()
        self.formManager = FormManager()
        self.controlManager = ControlManager()
        self.listenEvents()

    def listenEvents(self):
        self.ListenForEvent(c.GetEngineNamespace(), c.GetEngineSystemName(), "UiInitFinished", self, self.UIInit)
        self.ListenForEvent(Namespace, SystemNameServer, "applyObservableUpdate", self, self.applyObservableUpdate)
        self.ListenForEvent(Namespace, SystemNameServer, "registerControl", self, self.registerControl)
        self.ListenForEvent(Namespace, SystemNameServer, "showForm", self, self.showForm)

    def UIInit(self, data):
        from ..general.controls.oreui import OreUI
        OreUI()
        from ..config import Namespace
        c.RegisterUI(Namespace, "screen", Client.__module__.split("system")[0] + "ui.screen.Screen", "fui.screen")
        print("[INFO] FormUI registered.")

    def applyObservableUpdate(self, data):
        id = data['id']
        value = data['value']
        topScreen = c.GetTopScreen()
        if topScreen:
            if isFormScreen(topScreen):
                topScreen.applyObservableUpdate(id, value)
        else:
            raise Exception("获取TopScreen失败。")
        
    def registerControl(self, data):
        self.controlManager.create(data['type'], data['name'], data['path'], data['options'])

    def showForm(self, data):
        topScreen = c.GetTopScreen()
        if isFormScreen(topScreen):
            topScreen.addForm(data)
        else:
            c.PushScreen(Namespace, "screen", {})
            def pushFormScreen():
                topScreen = c.GetTopScreen()
                if isFormScreen(topScreen) and topScreen.isAllReady():
                    c.GetEngineCompFactory().CreateGame(c.GetLevelId()).CancelTimer(timerId)
                    topScreen.addForm(data)
            timerId = c.GetEngineCompFactory().CreateGame(c.GetLevelId()).AddRepeatedTimer(0.05, pushFormScreen)
