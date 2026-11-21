"""Static-only public API examples; checked with mypy, not executed in game."""
from typing import Any, Callable, Literal, assert_type
from FormUI.lib import (
    Button, Control, ControlType, Custom, Dropdown, Form, Group, Label,
    Observable, Screen, Slider, InnerStyles, Theme,
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
    assert_type(args.style, dict[str, Any])


def on_update(args: ObservableUpdateArguments) -> None:
    assert_type(args.key, str)
    if args.control is not None:
        args.control.GetChildByPath('/label').asLabel().SetText(str(args.newValue))


def on_close(args: FormShowResultArgs) -> None:
    assert_type(args.playerId, str)
    assert_type(args.closeReason, str)


def example() -> None:
    Theme.register('demo:theme', {'button': {'height': 36}, 'label': 'oreui:label'}, base='fluent')
    assert_type(Theme.get('demo:theme'), dict[str, dict[str, Any]])
    assert_type(Theme.names(), list[str])
    Screen.setDefaultTheme('demo:theme')
    Screen.setGrid(columns=[1, 2], rows=4, gap=6, padding=8)
    grid_form = Form.create('Grid', theme='demo:theme',
                            grid={'row': 0, 'column': 0, 'columnSpan': 2},
                            layout={'columns': 2, 'rows': 3, 'gap': 4})
    grid_form.button('Button', grid={'row': 0, 'column': 1})
    grid_form.custom(style={'class': 'demo:custom', 'grid': {'row': 1, 'column': 0}})
    grid_form.group(style={'class': 'demo:group', 'layout': {'columns': 2, 'rows': 1}},
                    grid={'row': 2, 'column': 0, 'columnSpan': 2})
    Form.create('Legacy content', grid={'row': 1, 'column': 0}, layout=False)
    Screen.clearGrid()
    Screen.setDefaultTheme()
    Theme.unregister('demo:theme')
    themed = Form.create('简洁调用', theme='fluent-dark')
    count = Observable.create(0)
    assert_type(count.map(lambda current: str(current)), ObservableValue[str])
    assert_type(count.watch(lambda current: _ignore(current)), Callable[[], None])
    count.update(lambda current: current + 1)
    themed.button('增加', lambda player: count.update(lambda current: current + 1))
    assert_type(themed.isAnyShowing(), bool)
    assert_type(themed.getShowingPlayers(), list[str])
    themed.show((player for player in ['p1']), onClose=on_close)
    assert_type(Screen.getDefaultStyle(ControlType.Button), dict[str, Any])
    Screen.closeAllForms()
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
    assert_type(form.group(children, style, {'id': 'group'}), FormInstance)
    form.button('confirm', {'onClick': lambda player: _ignore(assert_type(player, str))}, {'height': 30}, {'id': 'confirm'})
    form.toggle('running', visible, params={'id': 'running'})
    form.slider('angle', angle, maxValue=360, params={'angle': angle})
    form.textfield('title', text, params={'id': 'title'})
    form.label(text, {'fontSize': Observable.create(1.5)}, {'id': 'label'})
    form.divider({}, {'id': 'divider'})
    font_size: ObservableValue[float | str] = Observable.create(1.0)
    form.label(text, {'fontSize': font_size})
    font_size.setValue('default')
    form.dropdown('mode', [{'label': 'one', 'value': 1}], Observable.create(1), params={'id': 'mode'})
    form.custom({'nested': {'angle': angle}}, {'height': 40})
    result = form.show(['player'])
    assert_type(result, FormShowResult)
    assert_type(result.onClose(on_close), None)
    assert_type(form.close('player'), None)
    Screen.setDefaultStyle(ControlType.Group, {'size': ['100%', 60]})
    Screen.setDefaultStyle(ControlType.ScrollingPanel, {'grids': [1, 2]})
