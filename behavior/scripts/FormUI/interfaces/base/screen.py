# -*- coding: utf-8 -*-

class Screen:
    """屏幕管理"""

    @staticmethod
    def setDefaultStyle(controlType, style):
        from ...core.utils.environment import getSystem
        getSystem().screen.setDefaultStyle(controlType, style)

    @staticmethod
    def closeAllForms(target):
        from ...core.utils.environment import getSystem
        getSystem().screen.closeAllForms(target)
