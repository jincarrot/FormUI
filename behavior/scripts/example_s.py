# -*- coding: utf-8 -*-
import mod.server.extraServerApi as serverApi

ServerSystem = serverApi.GetServerSystemCls()
comp = serverApi.GetEngineCompFactory()
from FormUI.lib import *

class ExampleServer(ServerSystem):

    def __init__(self, namespace, systemName):
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "ServerChatEvent", self, self.example)

    def example(self, data):
        def click():
            title.setValue("click")
        def moveIn():
            title.setValue("moveIn")
        def moveOut():
            title.setValue("moveOut")
        playerId = data['playerId']
        title = Observable.create("111")
        label = Observable.create("222")
        form = Form.create(title, {"columns": [1]})
        form.button(label, {"onClick": click}, {"class": "oreui:green_btn_thin", "width": "100%"})
        form.button(label, {"onMoveIn": moveIn, "onMoveOut": moveOut}, {"class": "oreui:red_btn_thin", "width": "100%", "height": 50})
        form.button(label, {}, {"width": "100%"})
        form.button(label, {}, {"width": "100%"})
        form.button(label, {}, {"height": 30, "width": "100%"})
        form.button(label, {})
        form.button(label, {}, {"class": "oreui:green_btn"})
        form.button(label, {}, {"class": "oreui:green_btn", "width": "150%"})
        form.show(playerId)