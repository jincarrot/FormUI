# -*- coding: utf-8 -*-

class ControlType:
    """控件注册类"""

    def __init__(self, onCreate=None):
        self.onCreate = onCreate

class Divider(ControlType):
    """分割线注册类"""

    def __init__(self, onCreate=None):
        ControlType.__init__(self, onCreate)

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

    def __init__(self, onCreate=None, sliderPath="", labelPaths=["/label"], valuePaths=['/value']):
        ControlType.__init__(self, onCreate)
        self.sliderPath = sliderPath
        self.labelPaths = labelPaths
        self.valuePaths = valuePaths

class Textfield(ControlType):
    """文本输入框注册类"""
    
    def __init__(self, onCreate=None, textfieldPath="", labelPaths=["/label"]):
        ControlType.__init__(self, onCreate)
        self.textfieldPath = textfieldPath
        self.labelPaths = labelPaths

class Dropdown(ControlType):

    def __init__(self, onCreate=None, dropdownPath="", labelPaths=["/label"], boxLabelPaths=['/button_label'], itemLabelPaths=['/button_label'], contentPath="/content_panel", itemControl=""):
        ControlType.__init__(self, onCreate)
        self.labelPaths = labelPaths
        self.dropdownPath = dropdownPath
        self.boxLabelPaths = boxLabelPaths
        self.itemLabelPaths = itemLabelPaths
        self.contentPath = contentPath
        self.itemControl = itemControl

class Custom(ControlType):
    """自定义控件"""
    
    def __init__(self, onCreate=None, onObservableUpdate=None):
        ControlType.__init__(self, onCreate)
        self.onObservableUpdate = onObservableUpdate
