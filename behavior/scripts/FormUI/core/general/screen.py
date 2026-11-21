# -*- coding: utf-8 -*-
from ..utils.ui import getTopScreenNode, isFormScreen, normalizeTargets, STRING_TYPES
from ..utils.type import copyContainers
from ..utils.grid import validateGrid
from ..utils.theme import ThemeRegistry

from ..utils.environment import getSystem, isServer

class Screen(object):

    def __init__(self):
        self.__defaultStyles = {}
        self.__grid = None
        self.__theme = None
        self.themes = ThemeRegistry()

    def setGrid(self, columns=1, rows=1, gap=0, padding=0):
        self.__grid = validateGrid(dict(columns=columns, rows=rows, gap=gap, padding=padding))

    def getGrid(self):
        return copyContainers(self.__grid)

    def clearGrid(self):
        self.__grid = None

    def setDefaultTheme(self, name=None):
        if name is not None:
            self.themes.get(name)
        self.__theme = name

    def getDefaultTheme(self):
        return self.__theme

    @property
    def isFormUI(self):
        """
        返回当前顶层界面是否为表单界面。
        
        仅客户端可用。
        """
        return not isServer() and isFormScreen(getTopScreenNode())

    def closeAllForms(self, target=None):
        """
        关闭所有表单。
        """
        if isServer():
            if target is None:
                import mod.server.extraServerApi as s
                target = s.GetPlayerList()
            targets = normalizeTargets(target)
            if targets:
                getSystem().NotifyToMultiClients(targets, "closeForm", {"closeAll": True})
        else:
            getSystem().closeForm({"closeAll": True})

    def setDefaultStyle(self, controlType, style, sync=False):
        if not isinstance(controlType, STRING_TYPES) or not controlType:
            raise ValueError('controlType must be a nonempty string')
        if not isinstance(style, dict):
            raise TypeError('default style must be a dict')
        self.__defaultStyles[controlType] = copyContainers(style)
        if not sync:
            return
        if isServer():
            getSystem().BroadcastToAllClient("setDefaultStyle", {"controlType": controlType, "style": copyContainers(style)})
        else:
            getSystem().NotifyToServer("setDefaultStyle", {"controlType": controlType, "style": copyContainers(style)})

    def getDefaultStyle(self, controlType, defaultStyle=None):
        style = self.__defaultStyles.get(controlType, {})
        result = copyContainers(defaultStyle) if defaultStyle is not None else {}
        result.update(copyContainers(style))
        return result
