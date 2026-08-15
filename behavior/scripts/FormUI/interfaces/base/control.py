# -*- coding: utf-8 -*-

class Control:
    """自定义控件"""

    def __init__(self):
        raise Exception("Control类无法初始化。")

    @staticmethod
    def register(identifier, controlPath, control):
        from ...core.utils.environment import isServer
        controlType = control.__class__.__name__
        if hasattr(Control, "register" + controlType):
            options = {}
            for key in dir(control):
                if "__" in key:
                    continue
                try:
                    options[key] = getattr(control, key)
                except:
                    pass
                if key == "onCreate" and getattr(control, key) and isServer():
                    raise Exception("只有处于客户端环境时可以传入onCreate参数！")
            getattr(Control, "register" + controlType)(identifier, controlPath, options)
    
    @staticmethod
    def registerButton(identifier, path, options={}):
        """
        注册一个自定义按钮控件。
        """
        defaultOptions = {
            "labelPaths": ["/button_label"],
            "buttonPath": ""
        }
        defaultOptions.update(options)
        from ...core.utils.environment import getSystem, isServer
        from ...core.general.enums.controlType import ControlType
        system = getSystem()
        data = {
            "type": ControlType.Button,
            "name": identifier,
            "path": path,
            "options": defaultOptions
        }
        if isServer():
            system.BroadcastToAllClient("registerControl", data)
        getSystem().controlManager.create(ControlType.Button, identifier, path, defaultOptions)

    @staticmethod
    def registerScrollingPanel(identifier, path, options={}):
        """
        注册一个自定义面板控件。
        """
        defaultOptions = {
            "scrollingPanelPath": "",
            "titlePath": "",
            "closeBtnPath": ""
        }
        defaultOptions.update(options)
        from ...core.utils.environment import getSystem, isServer
        from ...core.general.enums.controlType import ControlType
        system = getSystem()
        data = {
            "type": ControlType.Panel,
            "name": identifier,
            "path": path,
            "options": defaultOptions
        }
        if isServer():
            system.BroadcastToAllClient("registerControl", data)
        getSystem().controlManager.create(ControlType.ScrollingPanel, identifier, path, options)

    @staticmethod
    def registerToggle(identifier, path, options={}):
        """
        注册一个自定义开关控件。
        """
        defaultOptions = {
            "togglePath": "/this_toggle",
            "labelPaths": [""]
        }
        defaultOptions.update(options)
        from ...core.utils.environment import getSystem, isServer
        from ...core.general.enums.controlType import ControlType
        system = getSystem()
        data = {
            "type": ControlType.Toggle,
            "name": identifier,
            "path": path,
            "options": defaultOptions
        }
        if isServer():
            system.BroadcastToAllClient("registerControl", data)
        getSystem().controlManager.create(ControlType.Toggle, identifier, path, options)

    @staticmethod
    def registerLabel(identifier, path, options={}):
        """
        注册一个自定义文本。
        """
        defaultOptions = {
            "labelPaths": ["/label"]
        }
        defaultOptions.update(options)
        from ...core.utils.environment import getSystem, isServer
        from ...core.general.enums.controlType import ControlType
        system = getSystem()
        data = {
            "type": ControlType.Label,
            "name": identifier,
            "path": path,
            "options": defaultOptions
        }
        if isServer():
            system.BroadcastToAllClient("registerControl", data)
        getSystem().controlManager.create(ControlType.Label, identifier, path, options)

    @staticmethod
    def registerDivider(identifier, path, options={}):
        """
        注册一个自定义分割线。
        """
        defaultOptions = {
        }
        defaultOptions.update(options)
        from ...core.utils.environment import getSystem, isServer
        from ...core.general.enums.controlType import ControlType
        system = getSystem()
        data = {
            "type": ControlType.Divider,
            "name": identifier,
            "path": path,
            "options": defaultOptions
        }
        if isServer():
            system.BroadcastToAllClient("registerControl", data)
        getSystem().controlManager.create(ControlType.Divider, identifier, path, options)

    @staticmethod
    def registerTextfield(identifier, path, options={}):
        """
        注册一个自定义输入框。
        """
        defaultOptions = {
            "labelPaths": "/label",
            "textfieldPath": "/textfield"
        }
        defaultOptions.update(options)
        from ...core.utils.environment import getSystem, isServer
        from ...core.general.enums.controlType import ControlType
        system = getSystem()
        data = {
            "type": ControlType.Textfield,
            "name": identifier,
            "path": path,
            "options": defaultOptions
        }
        if isServer():
            system.BroadcastToAllClient("registerControl", data)
        getSystem().controlManager.create(ControlType.Textfield, identifier, path, options)

    @staticmethod
    def registerSlider(identifier, path, options={}):
        """
        注册一个自定义滑动条。
        """
        defaultOptions = {
            "labelPaths": "/label",
            "sliderPath": "/slider",
            "valuePaths": ["/value"]
        }
        defaultOptions.update(options)
        from ...core.utils.environment import getSystem, isServer
        from ...core.general.enums.controlType import ControlType
        system = getSystem()
        data = {
            "type": ControlType.Slider,
            "name": identifier,
            "path": path,
            "options": defaultOptions
        }
        if isServer():
            system.BroadcastToAllClient("registerControl", data)
        getSystem().controlManager.create(ControlType.Slider, identifier, path, options)

    @staticmethod
    def registerDropdown(identifier, path, options={}):
        """
        注册一个自定义下拉框。
        """
        defaultOptions = {
            "labelPaths": "/button_label",
            "dropdownPath": "/dropdown_box",
            "boxLabelPaths": ["/button_label"],
            "itemLabelPaths": ["/button_label"],
            "contentPath": "/content_panel",
            "itemControl": ""
        }
        defaultOptions.update(options)
        from ...core.utils.environment import getSystem, isServer
        from ...core.general.enums.controlType import ControlType
        system = getSystem()
        data = {
            "type": ControlType.Dropdown,
            "name": identifier,
            "path": path,
            "options": defaultOptions
        }
        if isServer():
            system.BroadcastToAllClient("registerControl", data)
        getSystem().controlManager.create(ControlType.Dropdown, identifier, path, options)

    @staticmethod
    def registerCustom(identifier, path, options={}):
        """
        注册一个自定义控件。
        """
        from ...core.utils.environment import getSystem, isServer
        from ...core.general.enums.controlType import ControlType
        system = getSystem()
        data = {
            "type": ControlType.Custom,
            "name": identifier,
            "path": path,
            "options": options
        }
        if isServer():
            system.BroadcastToAllClient("registerControl", data)
        getSystem().controlManager.create(ControlType.Custom, identifier, path, options)
