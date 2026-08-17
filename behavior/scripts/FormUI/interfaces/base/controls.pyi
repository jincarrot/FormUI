# -*- coding: utf-8 -*-

from typing import Callable

from ...core.utils.type import CreateArguments, ObservableUpdateArguments

class ControlType:
    """控件注册类"""

class Button(ControlType):
    """按钮注册类"""

    def __init__(self, onCreate: Callable[[CreateArguments], None]=None, labelPaths: str | list[str]=["/button_label"], buttonPath: str=""):
        pass

class ScrollingPanel(ControlType):
    """滚动面板注册类"""

    def __init__(self, onCreate: Callable[[CreateArguments], None]=None, scrollingPanelPath: str="", titlePath: str="", closeBtnPath: str=""):
        pass

class Toggle(ControlType):
    """开关注册类"""

    def __init__(self, onCreate: Callable[[CreateArguments], None]=None, togglePath: str="/this_toggle", labelPaths: str | list[str]=["/label"]):
        pass

class Slider(ControlType):
    """滑动条注册类"""

    def __init__(self, onCreate: Callable[[CreateArguments], None]=None, sliderPath: str="", labelPaths: str | list[str]=["/label"]):
        pass

class Textfield(ControlType):
    """文本输入框注册类"""
    
    def __init__(self, onCreate: Callable[[CreateArguments], None]=None, textfieldPath: str="", labelPaths: str | list[str]=["/label"]):
        pass

class Custom(ControlType):
    """自定义控件"""
    
    def __init__(self, onCreate: Callable[[CreateArguments], None]=None, onObservableUpdate: Callable[[ObservableUpdateArguments], None]=None):
        pass
