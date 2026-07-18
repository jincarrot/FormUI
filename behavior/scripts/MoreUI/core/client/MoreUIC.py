# coding=utf-8
import mod.client.extraClientApi as clientApi
from Forms import *

ClientSystem = clientApi.GetClientSystemCls()

CComp = clientApi.GetEngineCompFactory()

class MoreUIClient(ClientSystem):

    def __init__(self, namespace, systemName):
        ClientSystem.__init__(self, namespace, systemName)
        self.__ListenEvent()

    def __ListenEvent(self):
        self.ListenForEvent(NamespaceServer, SystemNameServer, "sendCustomForm", self, self.sendCustomForm)
        self.ListenForEvent(NamespaceServer, SystemNameServer, "updateCustomForm", self, self.updateCustomForm)
        self.ListenForEvent(NamespaceServer, SystemNameServer, "closeCustomForm", self, self.closeCustomForm)
        self.ListenForEvent(NamespaceServer, SystemNameServer, "combineCustomForm", self, self.combineCustomForm)
        self.ListenForEvent(NamespaceServer, SystemNameServer, "sendMoreCustomForm", self, self.sendMoreCustomForm)
        self.ListenForEvent(NamespaceServer, SystemNameServer, "closeMoreUI", self, self.closeMoreUI)
        self.ListenForEvent(NamespaceServer, SystemNameServer, "sendSidebarForm", self, self.sendSidebarForm)
        self.ListenForEvent(NamespaceServer, SystemNameServer, "closeSidebarForm", self, self.closeSidebarForm)
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(), "UiInitFinished", self, self.initUI)

    def initUI(self, data):
        path = MoreUIClient.__module__.replace("MoreUIC", "Forms")
        clientApi.RegisterUI("server_ui", "CustomForm", "%s.CustomFormUI" % path, "server_forms.custom_form")
        clientApi.RegisterUI("server_ui", "MoreUI", "%s.More" % path, "server_forms.moreui")
        clientApi.RegisterUI("server_ui", "BarForm", "%s.BarFormUI" % path, "server_forms.bar_form")
        clientApi.RegisterUI("server_ui", "SidebarForm", "%s.SidebarFormUI" % path, "server_forms.sidebar_form")

    def sendCustomForm(self, data):
        screen = clientApi.GetTopScreen()
        if hasattr(screen, "isMoreUI"):
            for form in screen.forms:
                if form.formId == data['formId']:
                    screen.GetBaseUIControl(form.basePath).SetVisible(True)
        if hasattr(screen, "update"):
            return
        if "direction" in data['options']:
            clientApi.PushScreen("server_ui", "BarForm", data)
        else:
            clientApi.PushScreen("server_ui", "CustomForm", data)

    def updateCustomForm(self, data):
        screen = clientApi.GetTopScreen()
        if hasattr(screen, "update"):
            screen.update(data)

    def closeCustomForm(self, data):
        screen = clientApi.GetTopScreen()
        if hasattr(screen, "onButtonClick"):
            clientApi.PopScreen()
        if hasattr(screen, "isMoreUI"):
            for form in screen.forms:
                if form.formId == data['formId']:
                    form.close({})

    def closeMoreUI(self, data):
        screen = clientApi.GetTopScreen()
        if hasattr(screen, "isMoreUI"):
            clientApi.PopScreen()

    def combineCustomForm(self, data):
        screen = clientApi.GetTopScreen()
        def main():
            if hasattr(screen, "isMoreUI"):
                clientApi.GetEngineCompFactory().CreateGame(clientApi.GetLevelId()).CancelTimer(mainId)
                fm = None
                if 'direction' in data['options']:
                    fm = BarFormUI("", "", data)
                else:
                    fm = CustomFormUI("", "", data)
                def repeat():
                    if screen.GetBaseUIControl("/screen"):
                        screen.combine(fm)
                        clientApi.GetEngineCompFactory().CreateGame(clientApi.GetLevelId()).CancelTimer(timerId)
                timerId = clientApi.GetEngineCompFactory().CreateGame(clientApi.GetLevelId()).AddTimer(0.01, repeat)
        mainId = clientApi.GetEngineCompFactory().CreateGame(clientApi.GetLevelId()).AddTimer(0.01, main)

    def sendMoreCustomForm(self, data):
        screen = clientApi.GetTopScreen()
        if not hasattr(screen, "isMoreUI"):
            clientApi.PushScreen("server_ui", "MoreUI", data)

    def sendSidebarForm(self, data):
        screen = clientApi.GetTopScreen()
        if not hasattr(screen, "isSidebar"):
            clientApi.PushScreen("server_ui", "SidebarForm", data)

    def closeSidebarForm(self, data):
        screen = clientApi.GetTopScreen()
        if hasattr(screen, "isSidebar"):
            clientApi.PopScreen()