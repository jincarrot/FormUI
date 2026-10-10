# -*- coding: utf-8 -*-
from ...core.general.interfaces.controls import ControlKind, ControlStyle, GroupStyle
from ...core.general.interfaces.form import FormStyle

class Screen:
    @staticmethod
    def setDefaultStyle(controlType: ControlKind, style: ControlStyle | GroupStyle | FormStyle) -> None: ...
    @staticmethod
    def closeAllForms(target: str | list[str]) -> None: ...
