# -*- coding: utf-8 -*-
from .FormUI.lib import Form, Observable


def _strength_bar(value):
    level = int(value)
    return '强度 %d/10  [%s%s]' % (level, '#' * level, '-' * (10 - level))


def create_attack_form():
    target = Observable.create('')
    strength = Observable.create(5)
    showBar = Observable.create(True)
    note = Observable.create('')

    form = Form.create(
        root='fui:panel',
        theme='fluent-dark',
        style={'width': '42%', 'height': '90%', 'offsetX': '-27%'},
        layout={'combineUI': True, 'columns': [3, 2], 'rows': [2, 5, 3, 6, 2, 3], 'gap': 2, 'padding': 3},
    )
    form.label(target.map(lambda entityId: '目标实体 ID：%s' % entityId),
               grid={'row': 0, 'column': 0, 'columnSpan': 2})
    form.slider('强度', strength, 0, 10, 1, grid={'row': 1, 'column': 0, 'columnSpan': 2})
    form.label(strength.map(_strength_bar), {'visible': showBar},
               grid={'row': 2, 'column': 0})
    form.button('强度 +1', lambda playerId: strength.update(lambda n: (int(n) + 1) % 11),
                grid={'row': 2, 'column': 1})
    form.textfield('备注', note, grid={'row': 3, 'column': 0, 'columnSpan': 2})
    form.label(note.map(lambda text: text or '（空备注）'),
               grid={'row': 4, 'column': 0, 'columnSpan': 2})
    form.toggle('显示强度条', showBar, grid={'row': 5, 'column': 0})
    form.button('关闭', lambda playerId: form.close(playerId), grid={'row': 5, 'column': 1})
    return form.bindTemplate('fui_generated_examples.attack'), target
