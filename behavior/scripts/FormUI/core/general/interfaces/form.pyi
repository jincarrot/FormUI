# -*- coding: utf-8 -*-
from typing import TypedDict
from .controls import BoolValue, Dimension
from ..observable import Observable

FormStyle = TypedDict("FormStyle", {
    "class": str,
    "offsetX": Dimension,
    "offsetY": Dimension,
    "width": Dimension,
    "height": Dimension,
    "grids": list[int | float],  # 非空，权重均为有限正数。
    "hideOtherForms": BoolValue,
    "layer": int | Observable[int],
    "visible": BoolValue,
}, total=False)
