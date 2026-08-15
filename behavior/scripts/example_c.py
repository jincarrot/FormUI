# -*- coding: utf-8 -*-
import mod.client.extraClientApi as clientApi
import FormUI.register # 客户端需要导入此以注册并使用MoreUI
import random
from FormUI.lib import *

ClientSystem = clientApi.GetClientSystemCls()

class ExampleClient(ClientSystem):
    def __init__(self, namespace, systemName):
        ClientSystem.__init__(self, namespace, systemName)
        self.ListenForEvent("FormUIExample", "ExampleServer", "test", self, self.example)

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
        title = Observable.create(111)
        label = Observable.create("222")
        state = Observable.create(True)
        height = Observable.create(30)
        state.subscribe(toggle)
        form = Form.create(title, {"columns": [1], "offsetX": height})
        form.button(label, {"onClick": click}, {"class": "oreui:green_btn_thin", "visible": height})
        form.button(label, {"onMoveIn": moveIn, "onMoveOut": moveOut}, {"class": "oreui:red_btn_thin", "height": height, "visible": height})
        form.toggle(label, state)
        # form.slider("test", height, 0, title, 1)
        form.label("line1\nline2\nline3")
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
        form.textfield(title, title)
        form.show()
