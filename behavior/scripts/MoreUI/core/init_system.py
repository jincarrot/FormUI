# coding=utf-8
import mod.server.extraServerApi as serverApi

class A:
    pass

from config_server import *
path = A.__module__
"""scripts.MoreUI.core.init_system"""
server_system_path = path.split("init_system")[0] + "server.MoreUIS.MoreUIServer"

serverApi.RegisterSystem(NamespaceServer, SystemNameServer, server_system_path)