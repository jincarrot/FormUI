# -*- coding: utf-8 -*-
from typing import TypedDict, TypeAlias
from .controls import BoolValue, Dimension
from ..observable import Observable
from .grid import GridPosition, FormLayout

FormTheme: TypeAlias = str  # Built-ins or a name registered through Theme.register.

FormStyle = TypedDict("FormStyle", {
    "class": str,
    "offsetX": Dimension,
    "offsetY": Dimension,
    "width": Dimension,
    "height": Dimension,
    "grids": list[int | float],  # 非空，权重均为有限正数。
    "grid": GridPosition,
    "layout": FormLayout,
    "hideOtherForms": BoolValue,
    "layer": int | Observable[int],
    "visible": BoolValue,
}, total=False)
