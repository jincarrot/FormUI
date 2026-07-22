# -*- coding: utf-8 -*-
"""OreUI style controls."""

class Control:
    path = ""
    typeId = ""
    options = {}

    def __init__(self):
        from ...utils.environment import getSystem
        identifier = "oreui:" + self.path.split(".")[-1]
        getSystem().controlManager.create(self.typeId, identifier, self.path, self.options)
        
class Button(Control):
    typeId = "button"
    options = {
        "labelPaths": ("/default/label", "/hover/label", "/pressed/label")
    }

class RedBtn(Button):
    path = "fui_ore_btns.red_btn"

class GreenBtn(Button):
    path = "fui_ore_btns.green_btn"

class NormalBtn(Button):
    path = "fui_ore_btns.normal_btn"

class RedBtnThin(Button):
    path = "fui_ore_btns.red_btn_thin"

class GreenBtnThin(Button):
    path = "fui_ore_btns.green_btn_thin"

class NormalBtnThin(Button):
    path = "fui_ore_btns.normal_btn_thin"

class LightPanel(Control):
    path = "fui_ore_panels.light_panel"
    typeId = "scrolling_panel"
    options = {
        "scrollingPanelPath": "/content",
        "titlePath": "/header/title",
        "closeBtnPath": "/header/close"
    }

class LightPanelThin(LightPanel):
    path = "fui_ore_panels.light_panel_thin"

class DarkPanelThin(LightPanel):
    path = "dui_ore_panels.dark_panel_thin"

class OreUI:
    """OreUI style controls."""

    def __init__(self):
        CONTROLS = [
            RedBtn,
            GreenBtn,
            NormalBtn,
            RedBtnThin,
            GreenBtnThin,
            NormalBtnThin,
            LightPanel,
            LightPanelThin,
            DarkPanelThin
        ]
        for control in CONTROLS:
            control()

OreUI()