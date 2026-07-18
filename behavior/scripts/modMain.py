# -*- coding: utf-8 -*-
from mod.common.mod import Mod
import mod.server.extraServerApi as serverApi
import mod.client.extraClientApi as clientApi

@Mod.Binding(name="MoreUI", version="0.0.1")
class MoreUI(object):
    @Mod.InitServer()
    def MoreUIServerInit(self):
        serverApi.RegisterSystem("MoreUIExample", "ExampleServer", "scripts.example_s.ExampleServer")

    @Mod.InitClient()
    def MoreUIClientInit(self):
        clientApi.RegisterSystem("MoreUIExample", "ExampleClient", "scripts.example_c.ExampleClient")
