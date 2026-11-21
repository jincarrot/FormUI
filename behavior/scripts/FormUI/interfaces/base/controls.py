# -*- coding: utf-8 -*-

def _copyPaths(paths):
    return list(paths) if isinstance(paths, (list, tuple)) else paths


class ControlType:
    """控件注册类"""

    def __init__(self, onCreate=None):
        if onCreate is not None and not callable(onCreate):
            raise TypeError('onCreate must be callable or None')
        self.onCreate = onCreate

class Divider(ControlType):
    """分割线注册类"""

    def __init__(self, onCreate=None):
        ControlType.__init__(self, onCreate)

class Button(ControlType):
    """按钮注册类"""

    def __init__(self, onCreate=None, labelPaths=["/button_label"], buttonPath=""):
        ControlType.__init__(self, onCreate)
        self.labelPaths = _copyPaths(labelPaths)
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
        self.labelPaths = _copyPaths(labelPaths)

class Slider(ControlType):
    """滑动条注册类"""

    def __init__(self, onCreate=None, sliderPath="", labelPaths=["/label"], valuePaths=['/value']):
        ControlType.__init__(self, onCreate)
        self.sliderPath = sliderPath
        self.labelPaths = _copyPaths(labelPaths)
        self.valuePaths = _copyPaths(valuePaths)

class Textfield(ControlType):
    """文本输入框注册类"""
    
    def __init__(self, onCreate=None, textfieldPath="", labelPaths=["/label"]):
        ControlType.__init__(self, onCreate)
        self.textfieldPath = textfieldPath
        self.labelPaths = _copyPaths(labelPaths)

class Dropdown(ControlType):

    def __init__(self, onCreate=None, dropdownPath="", labelPaths=["/label"], boxLabelPaths=['/button_label'], itemLabelPaths=['/button_label'], contentPath="/content_panel", itemControl=""):
        ControlType.__init__(self, onCreate)
        self.labelPaths = _copyPaths(labelPaths)
        self.dropdownPath = dropdownPath
        self.boxLabelPaths = _copyPaths(boxLabelPaths)
        self.itemLabelPaths = _copyPaths(itemLabelPaths)
        self.contentPath = contentPath
        self.itemControl = itemControl

class ListView(ControlType):
    """内部滚动的单选列表模板；selectedPath 指向行内选中标记。"""

    def __init__(self, onCreate=None, scrollingPanelPath='/content',
                 labelPaths=('/label',), emptyLabelPath='/empty',
                 itemControl='', itemButtonPath='', itemLabelPaths=('/button_label',),
                 selectedPath='/selected'):
        ControlType.__init__(self, onCreate)
        self.scrollingPanelPath = scrollingPanelPath
        self.labelPaths = _copyPaths(labelPaths)
        self.emptyLabelPath = emptyLabelPath
        self.itemControl = itemControl
        self.itemButtonPath = itemButtonPath
        self.itemLabelPaths = _copyPaths(itemLabelPaths)
        self.selectedPath = selectedPath

class Label(ControlType):

    def __init__(self, onCreate=None):
        ControlType.__init__(self, onCreate)

class Custom(ControlType):
    """自定义控件。onCreate 在布局后接收 control、screenNode、params。

    onObservableUpdate 接收同一实例的 control、screenNode、params 和 key、oldValue、newValue。
    params 为当前参数快照；嵌套 Observable 更新按顶层参数名通知，不传 Observable 对象。
    """
    
    def __init__(self, onCreate=None, onObservableUpdate=None):
        ControlType.__init__(self, onCreate)
        if onObservableUpdate is not None and not callable(onObservableUpdate):
            raise TypeError('onObservableUpdate must be callable or None')
        self.onObservableUpdate = onObservableUpdate


class Group(ControlType):
    """A named collection of registered controls, positioned relative to its root."""

    def __init__(self, controls, onCreate=None):
        from ...core.utils.group import validateGroupControls
        ControlType.__init__(self, onCreate)
        self.controls = validateGroupControls(controls)
