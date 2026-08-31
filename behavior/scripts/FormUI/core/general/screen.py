# -*- coding: utf-8 -*-
from ..utils.ui import isFormScreen

from ..utils.environment import getSystem, isServer

class Screen:

    def __init__(self):
        self.__defaultStyles = {}

    @property
    def isFormUI(self):
        """
        返回当前顶层界面是否为表单界面。
        
        仅客户端可用。
        """
        if isServer():
            return False
        else:
            import mod.client.extraClientApi as c
            topScreen = c.GetTopScreen()
            return isFormScreen(topScreen)

    def closeAllForms(self, target):
        """
        关闭所有表单。
        """
        if isinstance(target, str):
            target = [target]
        if isServer():
            getSystem().NotifyToMultiClients(target, "closeForm", {"closeAll": True})
        else:
            getSystem().closeForm({"closeAll": True})

    def setDefaultStyle(self, controlType, style, sync=False):
        self.__defaultStyles[controlType] = style
        if not sync:
            return
        if isServer():
            getSystem().BroadcastToAllClient("setDefaultStyle", {"controlType": controlType, "style": style})
        else:
            getSystem().NotifyToServer("setDefaultStyle", {"controlType": controlType, "style": style})

    def getDefaultStyle(self, controlType, defaultStyle={}):
        style = self.__defaultStyles.get(controlType, {})
        defaultStyle.update(style)
        return defaultStyle
