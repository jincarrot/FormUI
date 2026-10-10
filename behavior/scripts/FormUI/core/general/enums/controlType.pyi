# -*- coding: utf-8 -*-
from typing import Final, Literal

class ControlType:
    """控件类型字符串常量，可传给 Screen.setDefaultStyle。"""
    Button: Final[Literal["button"]]
    Panel: Final[Literal["panel"]]
    ScrollingPanel: Final[Literal["scrolling_panel"]]
    Toggle: Final[Literal["toggle"]]
    Label: Final[Literal["label"]]
    Textfield: Final[Literal["textfield"]]
    Slider: Final[Literal["slider"]]
    Dropdown: Final[Literal["dropdown"]]
    Custom: Final[Literal["custom"]]
    Group: Final[Literal["group"]]
    Divider: Final[Literal["divider"]]
