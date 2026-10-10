# -*- coding: utf-8 -*-
"""可独立导入的内置样式常量；导入时不会注册控件或访问游戏系统。"""
from .core.general.controls.innerStyles import (
    InnerStyles, OreUIStyles, FlutterStyles, FluentStyles,
)

__all__ = ["InnerStyles", "OreUIStyles", "FlutterStyles", "FluentStyles"]
