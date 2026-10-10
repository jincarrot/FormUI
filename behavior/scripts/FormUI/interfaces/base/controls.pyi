# -*- coding: utf-8 -*-
from typing import Callable, TypeAlias
from ...core.general.interfaces.controls import GroupDefinitions
from ...core.utils.type import CreateArguments, ObservableUpdateArguments

CreateCallback: TypeAlias = Callable[[CreateArguments], None]
UpdateCallback: TypeAlias = Callable[[ObservableUpdateArguments], None]
ControlPaths: TypeAlias = list[str] | tuple[str, ...]
LabelPaths: TypeAlias = str | ControlPaths

class ControlType:
    """控件注册描述，不是 lib.ControlType 中的控件类型字符串常量。"""
    onCreate: CreateCallback | None
    def __init__(self, onCreate: CreateCallback | None = None) -> None: ...

class Divider(ControlType):
    def __init__(self, onCreate: CreateCallback | None = None) -> None: ...

class Button(ControlType):
    labelPaths: LabelPaths
    buttonPath: str
    def __init__(self, onCreate: CreateCallback | None = None, labelPaths: LabelPaths = ..., buttonPath: str = "") -> None: ...

class ScrollingPanel(ControlType):
    scrollingPanelPath: str
    titlePath: str
    closeBtnPath: str
    def __init__(self, onCreate: CreateCallback | None = None, scrollingPanelPath: str = "", titlePath: str = "", closeBtnPath: str = "") -> None: ...

class Toggle(ControlType):
    togglePath: str
    labelPaths: LabelPaths
    def __init__(self, onCreate: CreateCallback | None = None, togglePath: str = "/this_toggle", labelPaths: LabelPaths = ...) -> None: ...

class Slider(ControlType):
    sliderPath: str
    labelPaths: LabelPaths
    valuePaths: ControlPaths
    def __init__(self, onCreate: CreateCallback | None = None, sliderPath: str = "", labelPaths: LabelPaths = ..., valuePaths: ControlPaths = ...) -> None: ...

class Textfield(ControlType):
    textfieldPath: str
    labelPaths: LabelPaths
    def __init__(self, onCreate: CreateCallback | None = None, textfieldPath: str = "", labelPaths: LabelPaths = ...) -> None: ...

class Dropdown(ControlType):
    dropdownPath: str
    labelPaths: LabelPaths
    boxLabelPaths: ControlPaths
    itemLabelPaths: ControlPaths
    contentPath: str
    itemControl: str
    def __init__(self, onCreate: CreateCallback | None = None, dropdownPath: str = "", labelPaths: LabelPaths = ..., boxLabelPaths: ControlPaths = ..., itemLabelPaths: ControlPaths = ..., contentPath: str = "/content_panel", itemControl: str = "") -> None: ...

class Label(ControlType):
    def __init__(self, onCreate: CreateCallback | None = None) -> None: ...

class Custom(ControlType):
    """创建与更新回调均在客户端执行，参数提供原生控件和参数快照。"""
    onObservableUpdate: UpdateCallback | None
    def __init__(self, onCreate: CreateCallback | None = None, onObservableUpdate: UpdateCallback | None = None) -> None: ...

class Group(ControlType):
    """每个命名子控件的 class 必填，独立轴属性覆盖 offset/size。"""
    controls: GroupDefinitions
    def __init__(self, controls: GroupDefinitions, onCreate: CreateCallback | None = None) -> None: ...
