# coding=utf-8
"""
客户端注册，导入即可。
"""
import mod.client.extraClientApi as clientApi

class A:
    pass

from core.config import *
path = A.__module__

client_system_path = path.split("register")[0] + "core.client.MoreUIC.MoreUIClient"

clientApi.RegisterSystem(Namespace, SystemNameClient, client_system_path)