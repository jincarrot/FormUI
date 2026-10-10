# -*- coding: utf-8 -*-
from typing import Any
from .controls import ControlType

class Control:
    def __init__(self) -> None: ...
    @staticmethod
    def register(identifier: str, controlPath: str, control: ControlType) -> None:
        """使用注册描述类注册模板，支持 Group、Custom 和标准控件。"""
        ...

    @staticmethod
    def registerButton(identifier: str, path: str, options: dict[str, Any] = ...) -> None: ...

    @staticmethod
    def registerScrollingPanel(identifier: str, path: str, options: dict[str, Any] = ...) -> None: ...

    @staticmethod
    def registerToggle(identifier: str, path: str, options: dict[str, Any] = ...) -> None: ...

    @staticmethod
    def registerLabel(identifier: str, path: str, options: dict[str, Any] = ...) -> None: ...

    @staticmethod
    def registerDivider(identifier: str, path: str, options: dict[str, Any] = ...) -> None: ...

    @staticmethod
    def registerTextfield(identifier: str, path: str, options: dict[str, Any] = ...) -> None: ...

    @staticmethod
    def registerSlider(identifier: str, path: str, options: dict[str, Any] = ...) -> None: ...

    @staticmethod
    def registerDropdown(identifier: str, path: str, options: dict[str, Any] = ...) -> None: ...

    @staticmethod
    def registerCustom(identifier: str, path: str, options: dict[str, Any] = ...) -> None: ...

    @staticmethod
    def registerGroup(identifier: str, path: str, options: dict[str, Any] = ...) -> None: ...
