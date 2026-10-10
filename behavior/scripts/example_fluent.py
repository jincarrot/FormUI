# -*- coding: utf-8 -*-
"""Fluent window preview built through the public form interfaces."""
from FormUI.lib import Form, Observable


def create_fluent_form(dark=False):
    prefix = 'fluent:dark_' if dark else 'fluent:'
    name = Observable.create('Steve')
    enabled = Observable.create(True)
    volume = Observable.create(60)
    quality = Observable.create(1)
    status = Observable.create('点击按钮查看反馈，修改输入框实时更新名称。')
    form = Form.create('Fluent Qt / ' + ('Dark' if dark else 'Light'), {
        'class': 'fluent:dark_panel' if dark else 'fluent:light_panel',
        'width': '100%y', 'height': '80%', 'grids': [1, 1]
    })

    def style(control, **values):
        result = {'class': prefix + control, 'width': '100%-12px', 'offsetX': 6,
                  'height': 'default'}
        result.update(values)
        return result

    def clicked(control):
        return lambda player: status.setValue('%s 点击，playerId=%s' % (control, player))

    form.label('设置与偏好', style('label', height=30, fontSize=1.5))
    form.label(status, style('label', height=30))
    form.button('保存设置', {'onClick': clicked('保存设置')}, style('primary_button'))
    form.button('恢复默认', {'onClick': clicked('恢复默认')}, style('button'))
    form.button('描边按钮', {'onClick': clicked('描边按钮')}, style('outlined_button'))
    form.button('了解更多', {'onClick': clicked('了解更多')}, style('hyperlink_button'))
    form.textfield('玩家名称', name, style('textfield'))
    form.dropdown('画质', [{'label': '流畅', 'value': 0}, {'label': '均衡', 'value': 1},
                          {'label': '精致', 'value': 2}], quality, style('dropdown'))
    form.toggle('启用音效', enabled, style('toggle'))
    form.slider('音量', volume, 0, 100, 1, style('slider'))
    form.divider(style('divider'))
    form.divider(style('divider'))
    form.label(name + ' / 实时预览', style('label', height=30))
    form.label('标题栏仅保留关闭按钮。', style('label', height=30))
    form.button('音效已启用', {'onClick': clicked('音效')}, style('button', visible=enabled))
    form.button('关闭窗口', {'onClick': lambda player: form.close(player)}, style('danger_button'))
    return form
