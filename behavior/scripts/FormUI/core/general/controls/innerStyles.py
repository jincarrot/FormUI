# -*- coding: utf-8 -*-

class OreUIStyles:
    GreenBtn = "oreui:green_btn_thin"
    GreenBtnBold = "oreui:green_btn"
    RedBtn = "oreui:red_btn_thin"
    RedBtnBold = "oreui:red_btn"
    NormalBtn = "oreui:normal_btn_thin"
    NormalBtnBold = "oreui:normal_btn"
    LightPanel = "oreui:light_panel_thin"
    Label = "oreui:label"
    DividerIn = "oreui:divider_in"
    DividerOut = "oreui:divider_out"
    DividerDark = "oreui:divider_dark"
    DividerLight = "oreui:divider_light"
    Slider = "oreui:slider"
    Textfield = "oreui:textfield"
    Dropdown = "oreui:dropdown"

class FlutterStyles(object):
    """Flutter / Material 风格的浅色、深色控件标识符。"""

    LightPanel = "flutter:light_panel"
    DarkPanel = "flutter:dark_panel"
    FilledBtn = "flutter:filled_button"
    TonalBtn = "flutter:tonal_button"
    OutlinedBtn = "flutter:outlined_button"
    TextBtn = "flutter:text_button"
    DangerBtn = "flutter:danger_button"
    Label = "flutter:label"
    Divider = "flutter:divider"
    Toggle = "flutter:toggle"
    Slider = "flutter:slider"
    Textfield = "flutter:textfield"
    Dropdown = "flutter:dropdown"
    DarkFilledBtn = "flutter:dark_filled_button"
    DarkTonalBtn = "flutter:dark_tonal_button"
    DarkOutlinedBtn = "flutter:dark_outlined_button"
    DarkTextBtn = "flutter:dark_text_button"
    DarkDangerBtn = "flutter:dark_danger_button"
    DarkLabel = "flutter:dark_label"
    DarkDivider = "flutter:dark_divider"
    DarkToggle = "flutter:dark_toggle"
    DarkSlider = "flutter:dark_slider"
    DarkTextfield = "flutter:dark_textfield"
    DarkDropdown = "flutter:dark_dropdown"


class FluentStyles(object):
    """Fluent Qt 风格的浅色、深色控件标识符。"""

    LightPanel = "fluent:light_panel"
    DarkPanel = "fluent:dark_panel"
    PrimaryBtn = "fluent:primary_button"
    NormalBtn = "fluent:button"
    OutlinedBtn = "fluent:outlined_button"
    HyperlinkBtn = "fluent:hyperlink_button"
    DangerBtn = "fluent:danger_button"
    Label = "fluent:label"
    Divider = "fluent:divider"
    Toggle = "fluent:toggle"
    Slider = "fluent:slider"
    Textfield = "fluent:textfield"
    Dropdown = "fluent:dropdown"
    DarkPrimaryBtn = "fluent:dark_primary_button"
    DarkNormalBtn = "fluent:dark_button"
    DarkOutlinedBtn = "fluent:dark_outlined_button"
    DarkHyperlinkBtn = "fluent:dark_hyperlink_button"
    DarkDangerBtn = "fluent:dark_danger_button"
    DarkLabel = "fluent:dark_label"
    DarkDivider = "fluent:dark_divider"
    DarkToggle = "fluent:dark_toggle"
    DarkSlider = "fluent:dark_slider"
    DarkTextfield = "fluent:dark_textfield"
    DarkDropdown = "fluent:dark_dropdown"


class InnerStyles:
    """内置控件类型"""

    oreui = OreUIStyles()
    """OreUI风格控件"""

    flutter = FlutterStyles()
    """Flutter / Material 风格控件"""

    fluent = FluentStyles()
    """Fluent Qt 风格控件"""
