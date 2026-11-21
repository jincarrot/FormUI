# -*- coding: utf-8 -*-
"""ListView usage shared by client and server demos."""
from FormUI.lib import Form, Observable


def create_listview_form(themeName='oreui', dark=False):
    theme = themeName + ('-dark' if dark and themeName != 'oreui' else '')
    initial = [{'label': '物品 %02d' % number, 'value': number} for number in range(1, 31)]
    items = Observable.create(initial)
    selected = Observable.create(None)
    status = selected.map(lambda new: '尚未选择' if new is None else '已选择物品：%s' % new)
    form = Form.create('ListView · %s' % themeName, {
        'width': '90%y', 'height': '90%', 'grids': [1],
    }, theme=theme)
    form.label('列表内部滚动；点击条目选择，下面的按钮演示数据更新。', {'height': 36})
    form.listview('物品列表', items, selected, {
        'height': 180, 'itemHeight': 32, 'emptyText': '列表已清空，点击恢复',
    })
    form.label(status, {'height': 28})
    form.button('只看偶数', lambda player: items.setValue(
        [item for item in initial if item['value'] % 2 == 0]))
    form.button('反转顺序', lambda player: items.update(lambda rows: list(reversed(rows))))
    form.button('选择第 10 项', lambda player: selected.setValue(10))
    form.button('清除选择', lambda player: selected.setValue(None))
    form.button('清空列表', lambda player: items.setValue([]))
    form.button('恢复列表', lambda player: items.setValue(list(initial)))
    form.button('关闭', lambda player: form.close(player))
    return form
