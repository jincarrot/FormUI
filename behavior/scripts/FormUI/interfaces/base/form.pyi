# -*- coding: utf-8 -*-
from ...core.general.form import Form as RealForm
from ...core.general.interfaces.form import FormStyle
from ...core.general.interfaces.controls import TextValue

class Form:
    """表单工厂；create 返回支持链式添加控件的实例。"""
    def __init__(self) -> None: ...
    @staticmethod
    def create(title: TextValue, style: FormStyle = ...) -> RealForm: ...
