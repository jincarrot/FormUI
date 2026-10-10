"""Static-only public API examples; checked with mypy, not executed in game."""
from typing import Any, Literal, assert_type
from FormUI.lib import (
    Button, Control, ControlType, Custom, Dropdown, Form, Group, Label,
    Observable, Screen, Slider, InnerStyles,
)
from FormUI.innerStyles import FlutterStyles, FluentStyles
from FormUI.core.general.observable import Observable as ObservableValue
from FormUI.core.general.form import Form as FormInstance, FormShowResult
from FormUI.core.general.interfaces.controls import GroupChildren, GroupControlStyle, GroupStyle
from FormUI.core.utils.type import CreateArguments, ObservableUpdateArguments, FormShowResultArgs


def _ignore(value: object) -> None:
    pass


def on_create(args: CreateArguments) -> None:
    assert_type(args.params, dict[str, Any])


def on_update(args: ObservableUpdateArguments) -> None:
    assert_type(args.key, str)
    if args.control is not None:
        args.control.GetChildByPath('/label').asLabel().SetText(str(args.newValue))


def on_close(args: FormShowResultArgs) -> None:
    assert_type(args.playerId, str)
    assert_type(args.closeReason, str)


def example() -> None:
    assert_type(InnerStyles.flutter.FilledBtn, Literal['flutter:filled_button'])
    assert_type(FluentStyles.DarkPanel, Literal['fluent:dark_panel'])
    Form.create('Fluent', {'class': InnerStyles.fluent.LightPanel}).button(
        '保存', style={'class': InnerStyles.fluent.PrimaryBtn})
    Form.create('Flutter', {'class': FlutterStyles.DarkPanel}).toggle(
        '启用', True, {'class': InnerStyles.flutter.DarkToggle})
    angle = Observable.create(0.0)
    text = Observable.create('title')
    visible = Observable.create(True)
    size = Observable.create(['100%', '50%'])
    assert_type(angle, ObservableValue[float])
    assert_type(angle.getValue(), float)
    assert_type(text.getValue(), str)
    assert_type(size.getValue(), list[str])
    angle.subscribe(lambda value: _ignore(assert_type(value, float)))
    assert_type(angle > 0.0, ObservableValue[bool])
    assert_type(bool(visible), bool)
    angle.setValue(45.0)

    child: GroupControlStyle = {
        'class': Observable.create('oreui:label'), 'size': size,
        'offset': [0, angle], 'width': '50%', 'visible': visible,
    }
    Control.register('demo:group', 'fui.group', Group({'label': child}, onCreate=on_create))
    Control.register('demo:label', 'fui_ore_base.label', Label())
    Control.register('demo:custom', 'fui.group', Custom(on_create, on_update))
    Control.register('demo:button', 'button.path', Button(labelPaths=('/label',)))
    Control.register('demo:slider', 'slider.path', Slider(valuePaths=['/value']))
    Control.register('demo:dropdown', 'dropdown.path', Dropdown(itemLabelPaths=['/label']))
    style: GroupStyle = {'width': 200, 'height': 60}
    children: GroupChildren = {
        'label': {'label': text},
        'button': {'callbacks': {'onClick': lambda player: _ignore(assert_type(player, str))}},
        'inner': {'children': {'angle': {'value': angle}}},
        'custom': {'params': {'angle': angle}},
    }
    form = Form.create('example', {'class': 'oreui:light_panel_thin'})
    assert_type(form, FormInstance)
    assert_type(form.group(children, style), FormInstance)
    form.button('confirm', {'onClick': lambda player: _ignore(assert_type(player, str))}, {'height': 30})
    form.toggle('running', visible)
    form.slider('angle', angle, maxValue=360)
    form.textfield('title', text)
    form.label(text, {'fontSize': Observable.create(1.5)})
    font_size: ObservableValue[float | str] = Observable.create(1.0)
    form.label(text, {'fontSize': font_size})
    font_size.setValue('default')
    form.dropdown('mode', [{'label': 'one', 'value': 1}], Observable.create(1))
    form.custom({'nested': {'angle': angle}}, {'height': 40})
    result = form.show(['player'])
    assert_type(result, FormShowResult)
    assert_type(result.onClose(on_close), None)
    assert_type(form.close('player'), None)
    Screen.setDefaultStyle(ControlType.Group, {'size': ['100%', 60]})
    Screen.setDefaultStyle(ControlType.ScrollingPanel, {'grids': [1, 2]})
