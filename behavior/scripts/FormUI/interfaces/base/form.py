# -*- coding: utf-8 -*-

class Form:
    """自定义表单"""

    def __init__(self):
        raise Exception("若要创建表单（Form），请使用Form.create。")
    
    @staticmethod
    def create(title, style=None, theme=None, grid=None, layout=None):
        """创建表单；grid 指定屏幕网格位置，layout 覆盖内容网格，False 使用顺序布局。"""
        from ...core.utils.environment import isServer, getClientSystem, getServerSystem
        from ...core.config import Namespace, SystemNameServer, SystemNameClient
        formManager = None
        if isServer():
            server = getServerSystem()
            if server:
                formManager = server.formManager
            else:
                raise Exception("无法获取服务端系统'%s:%s'，请检查配置。" % (Namespace, SystemNameServer))
        else:
            client = getClientSystem()
            if client:
                formManager = client.formManager
            else:
                raise Exception("无法获取客户端系统'%s:%s'，请检查配置。" % (Namespace, SystemNameClient))
        return formManager.create(title, style, theme, grid, layout)
