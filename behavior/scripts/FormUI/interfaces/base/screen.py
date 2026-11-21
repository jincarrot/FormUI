# -*- coding: utf-8 -*-

class Screen:
    """屏幕管理"""

    @staticmethod
    def setGrid(columns=1, rows=1, gap=0, padding=0):
        """设置新表单使用的全局网格；行列支持数量或权重列表。"""
        from ...core.utils.environment import getSystem
        getSystem().screen.setGrid(columns, rows, gap, padding)

    @staticmethod
    def getGrid():
        from ...core.utils.environment import getSystem
        return getSystem().screen.getGrid()

    @staticmethod
    def clearGrid():
        from ...core.utils.environment import getSystem
        getSystem().screen.clearGrid()

    @staticmethod
    def setDefaultTheme(name=None):
        """设置新表单的默认主题；None 清除。"""
        from ...core.utils.environment import getSystem
        getSystem().screen.setDefaultTheme(name)

    @staticmethod
    def getDefaultTheme():
        from ...core.utils.environment import getSystem
        return getSystem().screen.getDefaultTheme()

    @staticmethod
    def setDefaultStyle(controlType, style):
        from ...core.utils.environment import getSystem
        getSystem().screen.setDefaultStyle(controlType, style, True)

    @staticmethod
    def getDefaultStyle(controlType):
        """获取已配置的默认风格副本；修改副本不会改变全局配置。"""
        from ...core.utils.environment import getSystem
        return getSystem().screen.getDefaultStyle(controlType)

    @staticmethod
    def closeAllForms(target=None):
        from ...core.utils.environment import getSystem
        getSystem().screen.closeAllForms(target)
