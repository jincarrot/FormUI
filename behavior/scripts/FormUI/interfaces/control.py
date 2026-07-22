# -*- coding: utf-8 -*-

class Control:
    """自定义控件"""

    def __init__(self):
        raise Exception("Control类无法初始化。")
    
    @staticmethod
    def registerButton(identifier, path, options={}):
        """
        注册一个自定义按钮控件。
        """
        defaultOptions = {
            "labelPaths": ("/button_label") 
        }
        defaultOptions.update(options)
        from ..core.utils.environment import getSystem, isServer
        from ..core.general.enums.controlType import ControlType
        system = getSystem()
        data = {
            "type": ControlType.Button,
            "name": identifier,
            "path": path,
            "options": defaultOptions
        }
        if isServer():
            system.BroadcastToAllClient("registerControl", data)
        else:
            system.NotifyToServer("registerControl", data)
        getSystem().controlManager.create(ControlType.Button, identifier, path, defaultOptions)

    @staticmethod
    def registerScrollingPanel(identifier, path, options={}):
        """
        注册一个自定义面板控件。
        """
        defaultOptions = {
            "scrollingPanelPath": "",
            "titlePath": "",
            "closeBtnPath": ""
        }
        defaultOptions.update(options)
        from ..core.utils.environment import getSystem, isServer
        from ..core.general.enums.controlType import ControlType
        system = getSystem()
        data = {
            "type": ControlType.Panel,
            "name": identifier,
            "path": path,
            "options": defaultOptions
        }
        if isServer():
            system.BroadcastToAllClient("registerControl", data)
        else:
            system.NotifyToServer("registerControl", data)
        getSystem().controlManager.create(ControlType.ScrollingPanel, identifier, path, options)

