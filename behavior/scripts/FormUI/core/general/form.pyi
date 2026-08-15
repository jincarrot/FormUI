# -*- coding: utf-8 -*-
from typing import Callable

from ...interfaces.base.observable import Observable
from interfaces.controls import ControlStyle, ButtonCallbacks, DropdownItem
from interfaces.form import FormOptions

from ..utils.environment import *

class FormShowResult:
    """
    表单显示结果
    """
    def onClose(self, callback: Callable[[dict], None]):
        """
        当表单关闭时触发。

        callback: 回调函数，参数为表单对象
        """

class Form:
    """
    自定义表单类（客户端服务端通用）
    """

    def button(self, label: str | Observable, callbacks: ButtonCallbacks={}, style: ControlStyle={}) -> Form:
        """
        添加一个按钮。

        label: 按钮标签文本，支持Observable绑定

        callbacks: 按钮回调函数，支持onClick、onMoveIn、onMoveOut

        style: 按钮样式
        """
    
    def toggle(self, label: str | Observable, state: Observable, style: ControlStyle={}) -> Form:
        """
        添加一个开关。

        label: 开关标签文本，支持Observable绑定

        state: 开关状态，支持Observable绑定

        style: 开关样式
        """

    def divider(self, style: ControlStyle={}) -> Form: 
        """
        添加一个分割线。

        style: 分割线样式
        """

    def label(self, text: str | Observable, style: ControlStyle={}) -> Form: 
        """
        添加一个文本标签。

        text: 文本内容，支持Observable绑定

        style: 文本标签样式
        """

    def slider(
            self, 
            label: str | Observable, 
            value: Observable, 
            minValue: float | Observable=0.0, 
            maxValue: float | Observable=1.0, 
            step: float | Observable=1, 
            style: ControlStyle={}
        ) -> Form:
        """
        添加一个滑动条。

        value: 滑动条当前值，支持Observable绑定

        minValue: 滑动条最小值，支持Observable绑定

        maxValue: 滑动条最大值，支持Observable绑定

        step: 滑动条步长，支持Observable绑定

        style: 滑动条样式
        """

    def textfield(self, label: str | Observable, value: Observable, style: ControlStyle={}) -> Form: 
        """
        添加一个文本输入框。

        label: 输入框标签文本，支持Observable绑定

        value: 输入框当前值，支持Observable绑定

        style: 输入框样式
        """

    def dropdown(self, label: str | Observable, items: list[DropdownItem], value: Observable, style: ControlStyle={}) -> Form: 
        """
        添加一个下拉框。

        label: 下拉框标签文本，支持Observable绑定

        items: 下拉框选项列表

        value: 下拉框当前值，支持Observable绑定

        style: 下拉框样式
        """
    
    def __custom(self, params={}, style: ControlStyle={}) -> Form: ...

    def show(self, target: list[str] | str, options: FormOptions={}) -> FormShowResult:
        """
        显示表单。

        target: 要显示的表单目标，可填单个玩家id或玩家id列表

        options: 表单显示选项
        """

    def close(self) -> Form: 
        """
        关闭表单。
        
        closeAll: 是否关闭所有表单，默认为False
        """
