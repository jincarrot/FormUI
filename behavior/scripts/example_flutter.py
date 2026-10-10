# -*- coding: utf-8 -*-
"""Flutter-style preview, built entirely through public FormUI interfaces."""
from FormUI.lib import Form, Observable


def create_flutter_form(dark=False):
    prefix = 'flutter:dark_' if dark else 'flutter:'
    text = Observable.create('Hello, Material')
    enabled = Observable.create(True)
    volume = Observable.create(40)
    selected = Observable.create(0)
    status = Observable.create('体验圆角控件和 Observable 双向绑定。')
    form = Form.create('Flutter UI / ' + ('Dark' if dark else 'Light'), {
        'class': 'flutter:dark_panel' if dark else 'flutter:light_panel',
        'width': '78.2%y', 'height': '76.5%', 'grids': [1, 1],
    })

    def style(name, **values):
        result = {'class': prefix + name, 'width': '100%-10.2px', 'offsetX': 5.1}
        result.update(values)
        return result

    def clicked(name):
        return lambda player: status.setValue('%s 点击，playerId=%s' % (name, player))

    form.label('Material 3', style('label', height=30.6, fontSize=1.53))
    form.label(status, style('label', height=30.6))
    form.button('Filled · 主操作', {'onClick': clicked('Filled')}, style('filled_button'))
    form.button('Tonal · 次操作', {'onClick': clicked('Tonal')}, style('tonal_button'))
    form.button('Outlined · 描边', {'onClick': clicked('Outlined')}, style('outlined_button'))
    form.button('Text · 文字', {'onClick': clicked('Text')}, style('text_button'))
    form.textfield('名称', text, style('textfield'))
    form.dropdown('品质', [{'label': '流畅', 'value': 0}, {'label': '均衡', 'value': 1},
                           {'label': '精致', 'value': 2}], selected, style('dropdown'))
    form.toggle('启用效果', enabled, style('toggle'))
    form.slider('音量', volume, 0, 100, 1, style('slider'))
    form.divider(style('divider'))
    form.divider(style('divider'))
    form.label(text + ' / 实时预览', style('label', height=30.6))
    form.label('开关控制左下按钮的可见性。', style('label', height=30.6))
    form.button('Observable 控制可见性', {'onClick': clicked('可见按钮')},
                style('filled_button', visible=enabled))
    form.button('关闭', {'onClick': lambda player: form.close(player)}, style('danger_button'))
    return form
