# -*- coding: utf-8 -*-
from mod.common.mod import Mod

@Mod.Binding(name="FormUI", version="0.0.1")
class FormUI(object):
    @Mod.InitServer()
    def initServer(self):
        from .FormUI import lib  # 导入公开入口以注册 FormUI 服务端系统。

    @Mod.InitClient()
    def initClient(self):
        import mod.client.extraClientApi as clientApi
        clientApi.RegisterSystem("FormUIExample", "AttackFormClient", "scripts.attack_client.AttackFormClient")
