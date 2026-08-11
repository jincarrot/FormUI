# -*- coding: utf-8 -*-
from ...interfaces.observable import Observable
from interfaces.controls import ControlStyle

from ..utils.environment import *

class Form:
    """
    自定义表单类（客户端服务端通用）
    """

    def button(self, label: str | Observable, callbacks={}, style: ControlStyle={}): ...
    
    def toggle(self, label: str | Observable, state: Observable, style: ControlStyle={}): ...

    def divider(self, style: ControlStyle={}): ...

    def label(self, text: str | Observable, style: ControlStyle={}): ...

    def slider(
            self, 
            label: str | Observable, 
            value: Observable, 
            minValue: float | Observable=0.0, 
            maxValue: float | Observable=1.0, 
            step: float | Observable=1, 
            style: ControlStyle={}
        ): ...

    def textfield(self, label: str | Observable, value: Observable, style: ControlStyle={}): ...

    def dropdown(self, label: str | Observable, items: list, value: Observable, style: ControlStyle={}): ...
    
    def __custom(self, params={}, style: ControlStyle={}): ...

    def show(self, target: list[str] | str, options={}): ...
