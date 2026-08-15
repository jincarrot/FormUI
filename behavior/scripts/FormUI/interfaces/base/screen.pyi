# -*- coding: utf-8 -*-

from ...core.general.enums.controlType import ControlType
from ...core.general.interfaces.controls import ControlStyle


class Screen:
    """屏幕管理"""

    @staticmethod
    def setDefaultStyle(controlType: ControlType, style: ControlStyle) -> None:
        """设置默认控件"""

    @staticmethod
    def closeAllForms(target: str | list[str]) -> None:
        """关闭所有表单"""
