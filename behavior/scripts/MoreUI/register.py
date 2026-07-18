# coding=utf-8
import mod.client.extraClientApi as clientApi

class A:
    pass

from core.config_client import *
path = A.__module__
"""scripts.MoreUI.core.init_system"""
client_system_path = path.split("register")[0] + "core.client.MoreUIC.MoreUIClient"

clientApi.RegisterSystem(NamespaceClient, SystemNameClient, client_system_path)