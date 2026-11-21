# -*- coding: utf-8 -*-
import mod.client.extraClientApi as c
from weakref import WeakSet
from ..config import Namespace, SystemNameServer
from ..utils.ui import getTopScreenNode, isFormScreen, notifyFormClosed
from ..utils.bindings import FormBindings

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
        self.__embeddedScreens = {}
        self.__embeddedListeners = []
        self.__nextPanelId = 0
        self.__embeddedFrame = 0
        self.__destroying = False
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

    def _formScreenDestroyed(self, screen):
        self.__formScreens.discard(screen)
        for pending in list(self.__pendingForms):
            if pending['screen'] is screen:
                self._closePending(pending, 'user')

    def _closePending(self, pending, reason):
        if not any(entry is pending for entry in self.__pendingForms):
            return
        self.__pendingForms.remove(pending)
        if pending['timer'] is not None:
            c.GetEngineCompFactory().CreateGame(c.GetLevelId()).CancelTimer(pending['timer'])
        notifyFormClosed(self, pending['data']['formId']['value'], reason)

    def _formScreens(self):
        screens = list(self.__formScreens)
        top = getTopScreenNode()
        if isFormScreen(top) and top not in self.__formScreens:
            screens.append(top)
        return screens

    def applyObservableUpdate(self, data):
        obId = data['id']
        value = data['value']
        if hasattr(self.controlManager, 'applyObservableUpdate'):
            self.controlManager.applyObservableUpdate(obId, value)
        for pending in self.__pendingForms:
            bindings = pending['bindings']
            previous = bindings.update(obId, value)
            if previous:
                pending['customUpdates'].extend(bindings.customUpdates(obId, previous))
        for screen in self._formScreens():
            screen.applyObservableUpdate(obId, value)
        
    def registerControl(self, data):
        self.controlManager.create(data['type'], data['name'], data['path'], data['options'])

    def onButtonTrigger(self, data):
        form = self.formManager.get(data['formId'])
        if form:
            callback = form._btnCallbacks.get(data['callbackId'])
            if callback:
                callback(data['playerId'])

    def showForm(self, data):
        formId = data['formId']['value']
        if (any(pending['data']['formId']['value'] == formId for pending in self.__pendingForms)
                or any(formId in screen.forms for screen in self.__formScreens)):
            raise RuntimeError('该表单已经被显示出来了，关闭后才能再次调用 show()。')
        if data.get('options', {}).get('combineUI'):
            self._showEmbedded(data)
            return
        topScreen = getTopScreenNode()
        if isFormScreen(topScreen) and topScreen.isAllReady():
            topScreen.addForm(data)
        else:
            pending = {'data': data, 'bindings': FormBindings(data), 'customUpdates': [], 'timer': None, 'screen': None}
            self.__pendingForms.append(pending)
            def pushFormScreen(data):
                if not any(entry is pending for entry in self.__pendingForms):
                    if pending['timer'] is not None:
                        c.GetEngineCompFactory().CreateGame(c.GetLevelId()).CancelTimer(pending['timer'])
                    return
                topScreen = pending['screen'] or getTopScreenNode()
                if isFormScreen(topScreen) and topScreen.isAllReady():
                    c.GetEngineCompFactory().CreateGame(c.GetLevelId()).CancelTimer(pending['timer'])
                    self.__pendingForms.remove(pending)
                    topScreen.addForm(data, pending['customUpdates'])
            try:
                pending['screen'] = c.PushScreen(Namespace, "screen", {})
                pending['timer'] = c.GetEngineCompFactory().CreateGame(c.GetLevelId()).AddRepeatedTimer(0.05, pushFormScreen, data)
            except:
                self.__pendingForms.remove(pending)
                raise

    def _showEmbedded(self, data):
        screen = None
        try:
            host = getTopScreenNode()
            if self.__destroying:
                raise RuntimeError('FormUI client system is shutting down')
            if host is None:
                raise RuntimeError('combineUI requires a current ScreenNode')
            if isFormScreen(host):
                if not host.isAllReady():
                    raise RuntimeError('The current FormUI screen is not ready')
                host.addForm(data)
            else:
                screen = self._embeddedForHost(host)
                if screen is None:
                    screen = self._createEmbeddedScreen(host)
                if screen.popping:
                    raise RuntimeError('The current host screen is closing')
                screen.addForm(data)
        except Exception as error:
            if screen is not None and not screen.forms:
                self._releaseEmbeddedScreen(screen)
            if not data['fromServer']['value']:
                raise
            formId = data['formId']['value']
            print('[FormUI] Cannot mount form %s: %s' % (formId, error))
            notifyFormClosed(self, formId, 'unavailable')

    def _embeddedForHost(self, host):
        screen = self.__embeddedScreens.get(id(host))
        if screen is not None:
            return screen
        # Native screens can be returned through a different Python wrapper.
        for screen in self.__embeddedScreens.values():
            if screen.panelOn(host):
                return screen
        return None

    def _createEmbeddedScreen(self, host):
        from .ui.screen import EmbeddedScreen
        while True:
            self.__nextPanelId += 1
            name = 'formui_embedded_%s' % self.__nextPanelId
            if not host.GetBaseUIControl('/' + name):
                break
        panel = host.CreateChildControl('fui.embedded_root', name, None)
        if not panel:
            raise RuntimeError('The current ScreenNode could not create the FormUI panel')
        try:
            screen = EmbeddedScreen(self, host, panel, name)
            getName = getattr(c, 'GetTopUI', None)
            screen.hostName = getName() if getName is not None else None
            self.__embeddedScreens[id(host)] = screen
            self._registerFormScreen(screen)
            if len(self.__embeddedScreens) == 1:
                for event, callback in (('GameRenderTickEvent', self._updateEmbedded),
                                        ('PopScreenEvent', self._onScreenPopping)):
                    listener = (c.GetEngineNamespace(), c.GetEngineSystemName(), event, self, callback)
                    self.ListenForEvent(*listener)
                    self.__embeddedListeners.append(listener)
        except Exception:
            if id(host) in self.__embeddedScreens:
                self._releaseEmbeddedScreen(self.__embeddedScreens[id(host)])
            else:
                host.RemoveChildControl(panel)
            raise
        return screen

    def _onScreenPopping(self, data):
        host = getTopScreenNode()
        if host is not None:
            screen = self._embeddedForHost(host)
            names = (data.get('screenName'), data.get('screenDef'))
            if screen is not None and (not screen.hostName or screen.hostName in names):
                screen.popping = True

    def _updateEmbedded(self, data=None):
        # PopScreenEvent handles stack removals. Periodically catch a rebuilt canvas
        # even for a static form, without a native lookup on every idle frame.
        self.__embeddedFrame = (self.__embeddedFrame + 1) % 30
        for screen in list(self.__embeddedScreens.values()):
            if screen._destroyed:
                continue
            active = screen._hasFrameWork()
            if screen.popping or ((active or not self.__embeddedFrame) and not screen.panelOn(screen._hostNode)):
                self._releaseEmbeddedScreen(screen, hostGone=True)
            elif active:
                screen.Update()

    def _releaseEmbeddedScreen(self, screen, hostGone=False):
        host = screen._hostNode
        if self.__embeddedScreens.get(id(host)) is not screen:
            return
        del self.__embeddedScreens[id(host)]
        self.__formScreens.discard(screen)
        if not self.__embeddedScreens:
            for listener in self.__embeddedListeners:
                self.UnListenForEvent(*listener)
            self.__embeddedListeners = []
        try:
            if not hostGone:
                panel = screen.panelOn(host)
                if panel:
                    host.RemoveChildControl(panel)
        finally:
            screen._hostClosed()

    def appendFormControl(self, data):
        from copy import deepcopy
        for pending in self.__pendingForms:
            form = pending['data']
            if form['formId']['value'] == data['formId']:
                if data['index'] == len(form['controls']):
                    form['controls'].append(deepcopy(data['control']))
                    pending['bindings'] = FormBindings(form)
                return
        for screen in self._formScreens():
            if data['formId'] in screen.forms:
                screen.appendFormControl(data)

    def closeForm(self, data):
        closeAll = data.get("closeAll", False)
        screens = self._formScreens()
        if closeAll:
            mounted = [(screen, formId, form) for screen in screens for formId, form in screen.forms.items()]
        else:
            formId = data['formId']
            mounted = [(screen, formId, screen.forms[formId]) for screen in screens if formId in screen.forms]
        cancelledScreens = set()
        for pending in list(self.__pendingForms):
            formId = pending['data']['formId']['value']
            if not closeAll and formId != data['formId']:
                continue
            if isFormScreen(pending['screen']):
                cancelledScreens.add(pending['screen'])
            self._closePending(pending, 'api')
        for screen, formId, form in mounted:
            if screen.forms.get(formId) is form:
                screen._closeForm(formId, 'api')
        for screen in cancelledScreens:
            if not screen.forms and not any(p['screen'] is screen for p in self.__pendingForms):
                screen._requestPop()

    def Destroy(self):
        self.__destroying = True
        for screen in list(self.__embeddedScreens.values()):
            self._releaseEmbeddedScreen(screen)
        destroy = getattr(ClientSystem, 'Destroy', None)
        if destroy is not None:
            destroy(self)

    def setDefaultStyle(self, data):
        self.screen.setDefaultStyle(data['controlType'], data['style'])
