# -*- coding: utf-8 -*-
"""Custom theme + global window grid + local content grid, reusable on either side."""
from FormUI.lib import Form, Observable, Screen, Theme


def create_grid_form():
    Theme.register('example:grid', {
        'button': 'fluent:dark_outlined_button',
        'label': {'fontSize': 1.1},
    }, base='fluent-dark', replace=True)
    # The example restores the caller's global setting after capturing it in the form.
    previous = Screen.getGrid()
    Screen.setGrid(columns=12, rows=12, padding=6)
    try:
        form = Form.create('主题与 Grid 布局', theme='example:grid',
            grid={'row': 1, 'column': 1, 'rowSpan': 10, 'columnSpan': 10},
            layout={'columns': [1, 2], 'rows': [1, 4, 1], 'gap': 6, 'padding': 8})
    finally:
        if previous is None:
            Screen.clearGrid()
        else:
            Screen.setGrid(**previous)
    selected = Observable.create(None)
    form.label(selected.map(lambda value: '当前选择：%s' % ('未选择' if value is None else value)),
               grid={'row': 0, 'column': 0, 'columnSpan': 2})
    form.listview('跨两列的列表', [
        {'label': '第 %s 项' % index, 'value': index} for index in range(1, 21)
    ], selected, grid={'row': 1, 'column': 0, 'columnSpan': 2})
    form.button('选择第 10 项', lambda player: selected.setValue(10),
                grid={'row': 2, 'column': 0})
    form.button('关闭', lambda player: form.close(player),
                grid={'row': 2, 'column': 1})
    return form
