# -*- coding: utf-8 -*-
"""
FormUI
"""

from .core.utils.environment import registerSystem as _registerSystem
_registerSystem()

from .interfaces.base.control import Control
from .interfaces.base.controls import *
from .interfaces.base.form import Form
from .interfaces.base.observable import Observable
from .interfaces.base.screen import Screen
from .interfaces.base.theme import Theme
from .core.general.enums.controlType import ControlType
from .innerStyles import InnerStyles, OreUIStyles, FlutterStyles, FluentStyles
