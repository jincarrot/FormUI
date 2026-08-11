# -*- coding: utf-8 -*-
import math
import random

import mod.server.extraServerApi as serverApi

ServerSystem = serverApi.GetServerSystemCls()
comp = serverApi.GetEngineCompFactory()
from FormUI.lib import *

class ExampleServer(ServerSystem):

    def __init__(self, namespace, systemName):
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "ServerChatEvent", self, self.example1)

    def example1(self, data):
        self.BroadcastToAllClient("test", {})

    def example(self, data):
        def click():
            label.setValue("click")
        def moveIn():
            label.setValue("moveIn")
            state.setValue(True)
        def moveOut():
            label.setValue("moveOut")
            state.setValue(False)
        def toggle(new):
            title.setValue(random.randint(1, 100))
        playerId = data['playerId']
        title = Observable.create(111)
        label = Observable.create("222")
        state = Observable.create(True)
        height = Observable.create(30)
        state.onUpdate(toggle)
        form = Form.create(title, {"columns": [1], "offsetX": height})
        form.button(label, {"onClick": click}, {"class": "oreui:green_btn_thin", "visible": height})
        form.button(label, {"onMoveIn": moveIn, "onMoveOut": moveOut}, {"class": "oreui:red_btn_thin", "height": height, "visible": height})
        form.toggle(label, state)
        form.slider("test", height, 0, title, 1)
        form.dropdown(label, [
            {
                "label": "test1",
                "value": 0
            },
            {
                "label": "aaa",
                "value": 2
            }
        ], height)
        # form.textfield(title, title)
        form.show(playerId)
        