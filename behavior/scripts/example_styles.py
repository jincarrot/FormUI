# -*- coding: utf-8 -*-
"""Three simultaneous forms with identical content and shared Observable values."""
from FormUI.lib import Form, Observable
from FormUI.innerStyles import InnerStyles


class StyleComparison(object):
    """OreUI, Flutter and Fluent, arranged left to right on the same screen."""

    def __init__(self, schedule=None):
        self.schedule = schedule or self._schedule
        self.pending = []
        self.scheduled = False
        self.name = Observable.create('Steve')
        self.enabled = Observable.create(True)
        self.volume = Observable.create(60)
        self.quality = Observable.create(1)
        self.count = Observable.create(0)
        self.counterText = Observable.create('点击次数：0')
        self.status = Observable.create('三张表单共享同一组数据。')
        self.namePreview = self.name + ' / 实时预览'
        self.count.subscribe(lambda value: self.counterText.setValue('点击次数：%s' % value))
        self.forms = []

        themes = (
            ('OreUI', '-32%', {
                'panel': InnerStyles.oreui.LightPanel, 'button': InnerStyles.oreui.GreenBtn,
                'secondary': InnerStyles.oreui.NormalBtn, 'close': InnerStyles.oreui.RedBtn,
                'label': InnerStyles.oreui.Label, 'divider': InnerStyles.oreui.DividerIn,
                'toggle': 'oreui:toggle_thin', 'slider': InnerStyles.oreui.Slider,
                'textfield': InnerStyles.oreui.Textfield, 'dropdown': InnerStyles.oreui.Dropdown,
            }),
            ('Flutter', '0%', {
                'panel': InnerStyles.flutter.LightPanel, 'button': InnerStyles.flutter.FilledBtn,
                'secondary': InnerStyles.flutter.TonalBtn, 'close': InnerStyles.flutter.DangerBtn,
                'label': InnerStyles.flutter.Label, 'divider': InnerStyles.flutter.Divider,
                'toggle': InnerStyles.flutter.Toggle, 'slider': InnerStyles.flutter.Slider,
                'textfield': InnerStyles.flutter.Textfield, 'dropdown': InnerStyles.flutter.Dropdown,
            }),
            ('Fluent', '32%', {
                'panel': InnerStyles.fluent.LightPanel, 'button': InnerStyles.fluent.PrimaryBtn,
                'secondary': InnerStyles.fluent.NormalBtn, 'close': InnerStyles.fluent.DangerBtn,
                'label': InnerStyles.fluent.Label, 'divider': InnerStyles.fluent.Divider,
                'toggle': InnerStyles.fluent.Toggle, 'slider': InnerStyles.fluent.Slider,
                'textfield': InnerStyles.fluent.Textfield, 'dropdown': InnerStyles.fluent.Dropdown,
            }),
        )
        for title, offset, theme in themes:
            self.forms.append(self.create_form(title, offset, theme))

    def create_form(self, title, offset, theme):
        form = Form.create(title, {
            'class': theme['panel'], 'width': '30%', 'height': '88%',
            'offsetX': offset, 'offsetY': 0, 'grids': [1],
            'hideOtherForms': False, 'layer': 0, 'visible': True,
        })

        def style(kind, **values):
            result = {'class': theme[kind], 'width': '100%-8px', 'offsetX': 4,
                      'height': 'default'}
            result.update(values)
            return result

        # One builder ensures the content and control order match in all themes.
        form.label('设置与偏好', style('label', height=26))
        form.label(self.status, style('label', height=36))
        form.textfield('玩家名称', self.name, style('textfield'))
        form.dropdown('画质', [{'label': '流畅', 'value': 0}, {'label': '均衡', 'value': 1},
                              {'label': '精致', 'value': 2}], self.quality, style('dropdown'))
        form.toggle('启用音效', self.enabled, style('toggle'))
        form.slider('音量', self.volume, 0, 100, 1, style('slider'))
        form.divider(style('divider'))
        form.label(self.namePreview, style('label', height=26))
        form.label(self.counterText, style('label', height=26))
        form.button('点击 +1', {'onClick': self.increment}, style('button'))
        form.button('恢复默认', {'onClick': self.reset}, style('secondary'))
        form.button('关闭三张表单', {'onClick': self.close}, style('close'))
        return form

    def increment(self, playerId):
        self.count.setValue(self.count.getValue() + 1)
        self.status.setValue('点击者：%s' % playerId)

    def reset(self, playerId):
        self.name.setValue('Steve')
        self.enabled.setValue(True)
        self.volume.setValue(60)
        self.quality.setValue(1)
        self.count.setValue(0)
        self.status.setValue('已恢复默认设置。')

    def show(self):
        """Reopen any missing panel, retaining all forms and shared values."""
        opened = 0
        for form in self.forms:
            if not form.isShowing() and form not in self.pending:
                self.pending.append(form)
                opened += 1
        if not self.scheduled:
            self._showPending()
        return opened

    def _schedule(self, callback):
        import mod.client.extraClientApi as clientApi
        game = clientApi.GetEngineCompFactory().CreateGame(clientApi.GetLevelId())
        game.AddTimer(0.1, callback)

    def _screenReady(self):
        import mod.client.extraClientApi as clientApi
        screen = clientApi.GetTopScreen()
        return bool(screen and getattr(screen, 'isFormScreen', lambda: False)() and screen.isAllReady())

    def _showPending(self):
        self.scheduled = False
        while self.pending:
            # The first show may still be creating its ScreenNode. Wait before
            # adding the remaining forms, so all three use that same screen.
            if any(form.isShowing() for form in self.forms) and not self._screenReady():
                self.scheduled = True
                self.schedule(self._showPending)
                return
            form = self.pending.pop(0)
            if not form.isShowing():
                form.show()

    def close(self, playerId=None):
        self.pending[:] = []
        for form in self.forms:
            if form.isShowing(playerId):
                form.close(playerId)
