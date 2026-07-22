# -*- coding: utf-8 -*-

class Observable:
    """可观测变量"""
    
    def __init__(self):
        raise Exception("若要创建可观测变量（Observable），请使用Observable.create")
    
    @staticmethod
    def create(value):
        from ..core.utils.environment import isServer, getServerSystem, getClientSystem
        from ..core.config import Namespace, SystemNameServer, SystemNameClient
        observableManager = None
        if isServer():
            server = getServerSystem()
            if server:
                observableManager = server.observableManager
            else:
                raise Exception("无法获取服务端系统'%s:%s'，请检查配置。" % (Namespace, SystemNameServer))
        else:
            client = getClientSystem()
            if client:
                observableManager = client.observableManager
            else:
                raise Exception("无法获取客户端系统'%s:%s'，请检查配置。" % (Namespace, SystemNameClient))
        return observableManager.create(value)
    
