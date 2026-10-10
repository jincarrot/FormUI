# -*- coding: utf-8 -*-
import mod.client.extraClientApi as c
from weakref import WeakSet
from ..config import Namespace, SystemNameServer
from ..utils.ui import isFormScreen
from ..utils.type import updateWrappedObservable, getCustomObservableUpdates

ClientSystem = c.GetClientSystemCls()

class Client(ClientSystem):

    def __init__(self, namespace, systemName):
        ClientSystem.__init__(self, namespace, systemName)
        from ..general.managers.observable import ObservableManager
        from ..general.managers.form import FormManager
        from ..general.managers.control import ControlManager
        from ..general.screen import Screen
        self.observableManager = ObservableManager()
        self.formManager = FormManager()
        self.controlManager = ControlManager()
        self.screen = Screen()
        self.__formScreens = WeakSet()
        self.__pendingForms = []
        self.listenEvents()

    def listenEvents(self):
        self.ListenForEvent(c.GetEngineNamespace(), c.GetEngineSystemName(), "UiInitFinished", self, self.UIInit)
        self.ListenForEvent(Namespace, SystemNameServer, "applyObservableUpdate", self, self.applyObservableUpdate)
        self.ListenForEvent(Namespace, SystemNameServer, "registerControl", self, self.registerControl)
        self.ListenForEvent(Namespace, SystemNameServer, "showForm", self, self.showForm)
        self.ListenForEvent(Namespace, SystemNameServer, 'appendFormControl', self, self.appendFormControl)
        self.ListenForEvent(Namespace, SystemNameServer, "closeForm", self, self.closeForm)
        self.ListenForEvent(Namespace, SystemNameServer, "setDefaultStyle", self, self.setDefaultStyle)

    def UIInit(self, data):
        from ..general.controls.oreui import OreUI
        OreUI()
        from ..general.controls.flutter import FlutterUI
        FlutterUI()
        from ..general.controls.fluent import FluentUI
        FluentUI()
        from ..config import Namespace
        c.RegisterUI(Namespace, "screen", Client.__module__.split("system")[0] + "ui.screen.Screen", "fui.screen")
        self.NotifyToServer('requestControls', {'playerId': c.GetLocalPlayerId()})
        print("[INFO] FormUI registered.")

    def _registerFormScreen(self, screen):
        self.__formScreens.add(screen)

    def applyObservableUpdate(self, data):
        obId = data['id']
        value = data['value']
        if hasattr(self.controlManager, 'applyObservableUpdate'):
            self.controlManager.applyObservableUpdate(obId, value)
        for pending in self.__pendingForms:
            previous = updateWrappedObservable(pending['data'], obId, value)
            pending['customUpdates'].extend(getCustomObservableUpdates(pending['data'], previous, value))
        screens = list(self.__formScreens)
        topScreen = c.GetTopScreen()
        if isFormScreen(topScreen) and not any(screen is topScreen for screen in screens):
            screens.append(topScreen)
        for screen in screens:
            screen.applyObservableUpdate(obId, value)
        
    def registerControl(self, data):
        self.controlManager.create(data['type'], data['name'], data['path'], data['options'])

    def onButtonTrigger(self, data):
        form = self.formManager.get(data['formId'])
        if form:
            form._btnCallbacks[data['callbackId']](data['playerId'])

    def showForm(self, data):
        formId = data['formId']['value']
        if any(pending['data']['formId']['value'] == formId for pending in self.__pendingForms):
            raise RuntimeError('该表单已经被显示出来了，关闭后才能再次调用 show()。')
        topScreen = c.GetTopScreen()
        if isFormScreen(topScreen) and topScreen.isAllReady():
            topScreen.addForm(data)
        else:
            pending = {'data': data, 'customUpdates': [], 'timer': None}
            self.__pendingForms.append(pending)
            def pushFormScreen(data):
                if not any(entry is pending for entry in self.__pendingForms):
                    if pending['timer'] is not None:
                        c.GetEngineCompFactory().CreateGame(c.GetLevelId()).CancelTimer(pending['timer'])
                    return
                topScreen = c.GetTopScreen()
                if isFormScreen(topScreen) and topScreen.isAllReady():
                    c.GetEngineCompFactory().CreateGame(c.GetLevelId()).CancelTimer(pending['timer'])
                    self.__pendingForms.remove(pending)
                    topScreen.addForm(data, pending['customUpdates'])
            try:
                c.PushScreen(Namespace, "screen", {})
                pending['timer'] = c.GetEngineCompFactory().CreateGame(c.GetLevelId()).AddRepeatedTimer(0.05, pushFormScreen, data)
            except:
                self.__pendingForms.remove(pending)
                raise

    def appendFormControl(self, data):
        from copy import deepcopy
        for pending in self.__pendingForms:
            form = pending['data']
            if form['formId']['value'] == data['formId']:
                if data['index'] == len(form['controls']):
                    form['controls'].append(deepcopy(data['control']))
                return
        screens = list(self.__formScreens)
        top = c.GetTopScreen()
        if isFormScreen(top) and not any(screen is top for screen in screens):
            screens.append(top)
        for screen in screens:
            if data['formId'] in screen.forms:
                screen.appendFormControl(data)

    def closeForm(self, data):
        closeAll = data.get("closeAll", False)
        cancelled = False
        for pending in list(self.__pendingForms):
            formId = pending['data']['formId']['value']
            if not closeAll and formId != data['formId']:
                continue
            self.__pendingForms.remove(pending)
            cancelled = True
            if pending['timer'] is not None:
                c.GetEngineCompFactory().CreateGame(c.GetLevelId()).CancelTimer(pending['timer'])
            event = 'formClose%s' % formId
            payload = {'closeReason': 'api', 'playerId': c.GetLocalPlayerId()}
            self.NotifyToServer(event, payload)
            self.BroadcastEvent(event, payload)
        topScreen = c.GetTopScreen()
        if isFormScreen(topScreen):
            hadForms = bool(topScreen.forms)
            if closeAll:
                for formId in list(topScreen.forms):
                    topScreen.onClose({"AddTouchEventParams": {"formId": formId}, "closeByInterface": True})
            else:
                topScreen.onClose({"AddTouchEventParams": {"formId": data['formId']}, "closeByInterface": True})
            if cancelled and not hadForms and not self.__pendingForms and not topScreen.forms:
                c.PopScreen()

    def setDefaultStyle(self, data):
        self.screen.setDefaultStyle(data['controlType'], data['style'])
