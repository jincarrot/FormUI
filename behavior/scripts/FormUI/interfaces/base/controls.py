# -*- coding: utf-8 -*-

class ControlType:
    """控件注册类"""

    def __init__(self, onCreate=None):
        self.onCreate = onCreate

class Button(ControlType):
    """按钮注册类"""

    def __init__(self, onCreate=None, labelPaths=["/button_label"], buttonPath=""):
        ControlType.__init__(self, onCreate)
        self.labelPaths = labelPaths
        self.buttonPath = buttonPath

class ScrollingPanel(ControlType):
    """滚动面板注册类"""

    def __init__(self, onCreate=None, scrollingPanelPath="", titlePath="", closeBtnPath=""):
        ControlType.__init__(self, onCreate)
        self.scrollingPanelPath = scrollingPanelPath
        self.titlePath = titlePath
        self.closeBtnPath = closeBtnPath

class Toggle(ControlType):
    """开关注册类"""

    def __init__(self, onCreate=None, togglePath="/this_toggle", labelPaths=["/label"]):
        ControlType.__init__(self, onCreate)
        self.togglePath = togglePath
        self.labelPaths = labelPaths

class Slider(ControlType):
    """滑动条注册类"""

    def __init__(self, onCreate=None, sliderPath="", labelPaths=["/label"]):
        ControlType.__init__(self, onCreate)
        self.sliderPath = sliderPath
        self.labelPaths = labelPaths

class Textfield(ControlType):
    """文本输入框注册类"""
    
    def __init__(self, onCreate=None, textfieldPath="", labelPaths=["/label"]):
        ControlType.__init__(self, onCreate)
        self.textfieldPath = textfieldPath
        self.labelPaths = labelPaths

class Custom(ControlType):
    def __init__(self, onCreate=None):
        ControlType.__init__(self, onCreate)
