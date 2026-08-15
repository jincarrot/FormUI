# -*- coding: utf-8 -*-
from typing import Callable, TypedDict

from ..observable import Observable

class ControlStyle(TypedDict):
    """控件样式"""
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
    visible: bool | Observable
    """可见性"""

class ButtonCallbacks(TypedDict):
    onClick: Callable[[], None]
    """按钮按下并抬起时触发"""
    onMoveIn: Callable[[], None]
    """手指移动入按钮时触发"""
    onMoveOut: Callable[[], None]
    """手指移出按钮时触发"""

class DropdownItem(TypedDict):
    label: str
    """下拉框选项标签值"""
    value: int
    """选项对应索引值"""
    