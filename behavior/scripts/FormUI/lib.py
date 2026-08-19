# -*- coding: utf-8 -*-
from .core.utils.environment import isServer as __t
if __t():
    import core.init_system
else:
    import register

from .interfaces.base.control import Control
from .interfaces.base.controls import *
from .interfaces.base.form import Form
from .interfaces.base.observable import Observable
from .interfaces.base.screen import Screen
from .core.general.enums.controlType import ControlType
