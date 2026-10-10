# -*- coding: utf-8 -*-
from typing import Any, Callable, Literal, TypeAlias, TypedDict
from ..observable import Observable

# 数字为像素值；字符串支持百分比、default 等尺寸表达式。
Dimension: TypeAlias = int | float | str | Observable[int] | Observable[float] | Observable[str]
DimensionPair: TypeAlias = list[Dimension] | Observable[list[Any]]
TextValue: TypeAlias = str | Observable[str]
NumberValue: TypeAlias = int | float | Observable[int] | Observable[float]
FontSize: TypeAlias = (
    NumberValue | Literal['default'] | Observable[str] | Observable[int | float]
    | Observable[int | str] | Observable[float | str] | Observable[int | float | str]
)
BoolValue: TypeAlias = bool | Observable[bool]
PlayerCallback: TypeAlias = Callable[[str], None]
ControlKind: TypeAlias = Literal[
    "button", "panel", "scrolling_panel", "toggle", "label", "textfield",
    "slider", "dropdown", "custom", "group", "divider",
]

ControlStyle = TypedDict("ControlStyle", {
    "class": str,
    "offsetX": Dimension,
    "offsetY": Dimension,
    "width": Dimension,
    "height": Dimension,
    "visible": BoolValue,
    "fontSize": FontSize,
}, total=False)

class ButtonCallbacks(TypedDict, total=False):
    """每个事件均可省略；回调参数为触发事件的 playerId。"""
    onClick: PlayerCallback
    onMoveIn: PlayerCallback
    onMoveOut: PlayerCallback

class DropdownItem(TypedDict):
    """静态选项；label/value 不支持 Observable。"""
    label: str
    value: int | str

class _GroupLayout(TypedDict, total=False):
    """offset/size 在运行时校验为两元素列表；独立轴属性优先。"""
    offset: DimensionPair
    size: DimensionPair
    offsetX: Dimension
    offsetY: Dimension
    width: Dimension
    height: Dimension
    visible: BoolValue

_GroupRequired = TypedDict("_GroupRequired", {"class": str | Observable[str]})

class GroupControlStyle(_GroupRequired, _GroupLayout):
    """Group 注册定义：class 必填，其余字段可省略。"""

GroupStyle = TypedDict("GroupStyle", {
    "class": str,
    "offset": DimensionPair,
    "size": DimensionPair,
    "offsetX": Dimension,
    "offsetY": Dimension,
    "width": Dimension,
    "height": Dimension,
    "visible": BoolValue,
}, total=False)

class GroupChildData(TypedDict, total=False):
    """按子控件类型选择字段；嵌套组使用 children，custom 使用 params。"""
    label: TextValue
    callbacks: ButtonCallbacks
    state: BoolValue
    value: Any
    minValue: NumberValue
    maxValue: NumberValue
    step: NumberValue
    items: list[DropdownItem]
    params: dict[str, Any]
    children: dict[str, GroupChildData]

GroupDefinitions: TypeAlias = dict[str, GroupControlStyle]
GroupChildren: TypeAlias = dict[str, GroupChildData]
