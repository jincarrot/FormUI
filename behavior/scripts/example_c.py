# -*- coding: utf-8 -*-
import mod.client.extraClientApi as clientApi
import MoreUI.register # 客户端需要导入此以注册并使用MoreUI

ClientSystem = clientApi.GetClientSystemCls()

class ExampleClient(ClientSystem):
    pass
