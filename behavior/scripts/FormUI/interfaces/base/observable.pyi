# -*- coding: utf-8 -*-
from typing import TypeVar
from ...core.general.observable import Observable as ObservableValue

_T = TypeVar("_T")

class Observable:
    """Observable 工厂；create 返回带 getValue/setValue 的实际变量实例。"""
    def __init__(self) -> None: ...

    @staticmethod
    def create(value: _T) -> ObservableValue[_T]: ...
