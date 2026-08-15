# -*- coding: utf-8 -*-
from typing import TypedDict
from ..observable import Observable

class FormStyle(TypedDict):
    """表单创建样式"""
    Class: str
    """表单的背景控件名称，必须为ScrollingPanel（应为"class"而非"Class"）"""
    offsetX: float | str | Observable
    """表单的X轴方向（横向）位置偏移量"""
    offsetY: float | str | Observable
    """表单的Y轴方向（纵向）位置偏移量"""
    width: float | str | Observable
    """表单的宽度"""
    height: float | str | Observable
    """表单的高度"""
    columns: list[float]
    """
    表单的列数，控件将会根据此值进行排布。
    
    如，[1, 2, 1]意为3列，宽度比例为1:2:1
    """

class FormOptions(TypedDict):
    """表单创建选项"""
    hideOtherForms: bool
    """弹出时，隐藏其他表单"""
    layer: int
    """表单所处层级"""
    visible: bool
    """表单可见性"""
