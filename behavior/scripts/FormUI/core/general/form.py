# -*- coding: utf-8 -*-
from ..utils.environment import *

class Form:
    """
    自定义表单类（客户端服务端通用）
    """
    
    def __init__(self, id, title="", style={}):
        # type: (int, str, dict) -> None
        self.__id = id
        self.__title = title
        self.__controls = []
        defaultStyle = {
            "class": "oreui:light_panel_thin",
            "offsetX": 0,
            "offsetY": 0,
            "width": "40%",
            "height": "70%",
            "columns": [1]
        }
        defaultStyle.update(style)
        self.__style = defaultStyle
        self._btnCallbacks = {
            0: lambda: None
        }

    def button(self, label, callbacks={}, style={}):
        # type: (str, dict, dict) -> Form
        """
        添加一个按钮。
        """
        for key in callbacks:
            self._btnCallbacks[len(self._btnCallbacks)] = callbacks[key]
            callbacks[key] = len(self._btnCallbacks) - 1
        defaultCallbacks = {
            "onClick": 0,
            "onMoveIn": 0,
            "onMoveOut": 0
        }
        defaultStyle = {
            "class": "oreui:normal_btn_thin",
            "width": "100%-4px",
            "height": "default",
            "offsetX": 0,
            "offsetY": 0,
            "visible": True
        }
        defaultCallbacks.update(callbacks)
        defaultStyle.update(style)
        self.__controls.append({
            "label": label,
            "callbacks": defaultCallbacks,
            "style": defaultStyle
        })
        return self
    
    def toggle(self, label, state, style={}):
        """
        添加一个开关。
        """
        defaultStyle = {
            "class": "oreui:toggle_thin",
            "width": "100%-4px",
            "height": "default",
            "offsetX": 0,
            "offsetY": 0,
            "visible": True
        }
        defaultStyle.update(style)
        self.__controls.append({
            "label": label,
            "state": state,
            "style": defaultStyle
        })
        return self

    def divider(self, style={}):
        # type: (str, dict) -> Form
        """
        添加一个分割线。
        """
        defaultStyle = {
            "class": "oreui:divider_in",
            "width": "100%-4px",
            "height": 2,
            "offsetX": 0,
            "offsetY": 0,
            "visible": True
        }
        defaultStyle.update(style)
        self.__controls.append({
            "style": defaultStyle
        })
        return self

    def label(self, text, style={}):
        # type: (str, dict, dict) -> Form
        """
        添加一个按钮。
        """
        defaultStyle = {
            "class": "oreui:label",
            "width": "100%-4px",
            "height": "default",
            "offsetX": 0,
            "offsetY": 0,
            "visible": True,
            "fontSize": "default"
        }
        defaultStyle.update(style)
        self.__controls.append({
            "label": text,
            "style": defaultStyle
        })
        return self

    def slider(self, label, value, minValue=0.0, maxValue=1.0, step=1, style={}):
        """添加一个滑动条。"""
        defaultStyle = {
            "class": "oreui:slider",
            "width": "100%-4px",
            "height": "default",
            "offsetX": 0,
            "offsetY": 0,
            "visible": True
        }
        defaultStyle.update(style)
        self.__controls.append({
            "label": label,
            "value": value,
            "minValue": minValue,
            "maxValue": maxValue,
            "step": step,
            "style": defaultStyle
        })
        return self

    def textfield(self, label, value, style={}):
        defaultStyle = {
            "class": "oreui:textfield",
            "width": "100%-4px",
            "height": "default",
            "offsetX": 0,
            "offsetY": 0,
            "visible": True
        }
        defaultStyle.update(style)
        self.__controls.append({
            "label": label,
            "value": value,
            "style": defaultStyle
        })
        return self

    def dropdown(self, label, items, value, style={}):
        defaultStyle = {
            "class": "oreui:dropdown",
            "width": "100%-4px",
            "height": "default",
            "offsetX": 0,
            "offsetY": 0,
            "visible": True
        }
        defaultStyle.update(style)
        self.__controls.append({
            "label": label,
            "items": items,
            "value": value,
            "style": defaultStyle
        })
        return self
    
    def custom(self, params={}, style={}):
        pass

    def show(self, target, options={}):
        """
        显示表单。
        """
        defaultOptions = {
            "hideOtherForms": False,
            "layer": "top",
            "visible": True
        }
        defaultOptions.update(options)
        # Wrap data.
        from ..utils.type import wrapDict
        observables = []
        data = wrapDict({
            "formId": self.__id,
            "title": self.__title,
            "controls": self.__controls,
            "style": self.__style,
            "options": defaultOptions,
            "fromServer": isServer()
        }, observables)
        data['observables'] = observables
        # Send data.
        if isServer():
            if isinstance(target, str):
                getSystem().NotifyToClient(target, "showForm", data)
            else:
                getSystem().NotifyToMultiClients(target, "showForm", data)
        else:
            getSystem().showForm(data)
