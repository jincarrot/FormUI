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
        "labelPaths": ("/default/label", "/hover/label", "/pressed/label"),
        "buttonPath": "/button"
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
    path = "fui_ore_panels.dark_panel_thin"

class Toggle(Control):
    path = "fui_ore_chks.toggle_thin"
    typeId = "toggle"
    options = {
        "togglePath": "/toggle/this_toggle",
        "labelPaths": ["/label"]
    }

class Label(Control):
    path = "fui_ore_base.label"
    typeId = "label"
    options = {
        "labelPaths": ['/label']
    }

class DividerIn(Control):
    path = "fui_ore_base.divider_in"
    typeId = "divider"

class DividerOut(Control):
    path = "fui_ore_base.divider_out"
    typeId = "divider"

class DividerDark(Control):
    path = "fui_ore_base.divider_dark"
    typeId = "divider"

class DividerLight(Control):
    path = "fui_ore_base.divider_light"
    typeId = "divider"

class Slider(Control):
    path = "fui_ore_sliders.slider"
    typeId = "slider"
    options = {
        "labelPaths": ["/label"],
        "sliderPath": "/slider",
        "valuePaths": ["/value"]
    }

class Textfield(Control):
    path = "fui_ore_textfields.textfield"
    typeId = "textfield"
    options = {
        "labelPaths": ["/label"],
        "textfieldPath": "/textfield"
    }

class Dropdown(Control):
    path = "fui_ore_dropdowns.dropdown"
    typeId = "dropdown"
    options = {
        "labelPaths": "/label",
        "dropdownPath": "/dropdown_box",
        "contentPath": "/content_panel",
        "boxLabelPaths": ["/default/label", "/hover/label", "/pressed/label"],
        "itemLabelPaths": ["/button_label"],
        "itemControl": "fui_ore_dropdowns.dropdown_items"
    }

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
            DarkPanelThin,
            Toggle,
            Label,
            DividerIn,
            DividerOut,
            DividerDark,
            DividerLight,
            Slider,
            Textfield,
            Dropdown
        ]
        for control in CONTROLS:
            control()

OreUI()