# -*- coding: utf-8 -*-
from ...core.general.form import Form as RealForm
from ...core.general.interfaces.form import FormStyle

class Form:
    """自定义表单"""
    
    @staticmethod
    def create(title: str, style: FormStyle={}) -> RealForm:
        """创建一个表单。"""