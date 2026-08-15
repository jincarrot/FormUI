# -*- coding: utf-8 -*-
from behavior.scripts.FormUI.interfaces.base.controls import ControlType

class Control:
    """自定义控件"""

    @staticmethod
    def register(identifier: str, controlPath: str, control: ControlType) -> None: 
        """
        注册一个自定义控件。

        identifier: 控件名称，自定义，推荐“命名空间+控件名”，如"oreui:label"

        controlPath: 控件路径，在json文件中的定义，如“fui_ore_base.base_thin”

        control: 控件定义类，如Button(labelPaths = ["/button_label"])
        """
    