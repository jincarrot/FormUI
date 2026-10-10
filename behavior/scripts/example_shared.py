# -*- coding: utf-8 -*-
"""两端共用的功能展台；端相关事件与原生 UI 操作见 example_c/example_s。"""
from FormUI.lib import Control, Form, Group, Observable, Screen


def register_groups(prefix):
    """两端都可注册无原生回调的 Group，服务端的定义会补发给后来加入的玩家。"""
    Control.register(prefix + ':inner', 'fui.group', Group({
        'caption': {'class': 'oreui:label', 'offset': [0, 0], 'size': ['100%', 24]},
        'button': {'class': 'oreui:green_btn_thin', 'offset': [99, 99],
                   'offsetX': 0, 'offsetY': 28, 'size': ['100%', 30]},
    }))
    Control.register(prefix + ':group', 'fui.group', Group({
        'inner': {'class': prefix + ':inner', 'offset': [0, 0], 'size': ['100%', 64]},
        'menu': {'class': 'oreui:dropdown', 'offset': [0, 68], 'size': ['100%', 45]},
        'switch': {'class': 'oreui:toggle_thin', 'offset': [0, 117],
                   'width': '100%', 'height': 40, 'visible': True},
        'custom': {'class': 'example:custom_label', 'offset': [0, 161],
                   'size': ['100%', 52]},
    }))


class DemoSession(object):
    """每个玩家独立保存状态；两端调用的是同一套公开 FormUI 接口。"""

    def __init__(self, side, playerId, report, schedule):
        self.side = side
        self.playerId = playerId
        self.report = report
        self.schedule = schedule
        self.prefix = 'example_' + side
        self.key = side + ':' + playerId
        self.popups = []
        self.closedHooks = []
        self.reopen = False
        self.appended = 0
        self.showCount = 0
        self.createdAppend = False
        self.rangeIndex = 0
        self.fontIndex = 0
        self.subscribed = True
        self.status = Observable.create('操作控件，观察这里的旧值 / 新值和回调玩家。')
        self.title = Observable.create(('客户端' if side == 'client' else '服务端') + '功能展台')
        self.text = Observable.create('修改我，旁边的文本会同步变化')
        self.count = Observable.create(0)
        self.number = Observable.create(3.0)
        self.minimum = Observable.create(0.0)
        self.maximum = Observable.create(10.0)
        self.step = Observable.create(1.0)
        self.selected = Observable.create(0)
        self.otherSelected = Observable.create(1)
        self.visible = Observable.create(True)
        self.font = Observable.create(1.0)
        self.rootWidth = Observable.create('90%y')
        self.rootHeight = Observable.create('90%')
        self.rootX = Observable.create(0)
        self.rootY = Observable.create(0)
        self.groupSize = Observable.create(['100%-8px', 218])
        self.groupOffset = Observable.create([4, 0])
        self.palette = Observable.create({'color': [0.2, 0.2, 0.2]})
        self.history = Observable.create(['初始记录'])
        self.items = [{'label': '选项 %s' % i, 'value': i} for i in range(8)]

        # 算术、比较生成自动更新的 Observable；文本拼接见下面的 label。
        self.countText = Observable.create('点击次数：0')
        self.count.subscribe(lambda new: self.countText.setValue('点击次数：%s' % new))
        self.derivedWidth = 40 + self.count * 5
        self.derivedVisible = self.count >= 2
        self.onText = self._watch('文本', self.text)
        self.text.subscribe(self.onText)
        self.number.subscribe(self._watch('滑动条原始值', self.number))
        self.selected.subscribe(self._watch('左侧下拉', self.selected))
        self.otherSelected.subscribe(self._watch('右侧下拉', self.otherSelected))
        self.visible.subscribe(self._watch('可见性', self.visible))

        self.form = Form.create(self.title, {
            'class': 'oreui:light_panel_thin', 'grids': [1, 1],
            'width': self.rootWidth, 'height': self.rootHeight,
            'offsetX': self.rootX, 'offsetY': self.rootY,
        })
        self._build()

    def _watch(self, name, observable):
        def changed(new):
            # subscribe 回调发生在赋值前；不要把 getValue() 当成新值。
            self.status.setValue('%s：%s -> %s' % (name, observable.getValue(), new))
        return changed

    def _button(self, text, callback, style=None):
        self.form.button(text, {'onClick': callback}, style or {})

    def _build(self):
        form = self.form
        form.label(self.status, {'height': 60})
        form.label('每行两列；下拉菜单应覆盖下方控件，\n相邻列保持位置，内容可以滚动。', {'height': 60})
        form.dropdown('左侧长菜单', self.items, self.selected)
        form.dropdown('右侧长菜单', self.items, self.otherSelected)
        form.textfield('双向文本输入', self.text)
        form.label(self.text + ' / 自动联动', {'height': 40, 'fontSize': self.font})
        form.slider('动态边界滑动条', self.number, self.minimum, self.maximum, self.step)
        self._button('切换边界 / 连续模式', self.changeRange)
        form.toggle('显示 / 隐藏下方绿色按钮', self.visible)
        self._button('字体：1 -> 1.5 -> default', self.changeFont)
        self._button(self.countText, self.increment, {'class': 'oreui:green_btn_thin', 'visible': self.visible})
        form.label('点击两次后显示；宽度 = 40 + 次数 × 5', {
            'width': self.derivedWidth, 'height': 40, 'visible': self.derivedVisible,
        })
        form.button('点击 / 移入 / 移出回调', {
            'onClick': self.increment,
            'onMoveIn': lambda player: self.status.setValue('移入，playerId=' + player),
            'onMoveOut': lambda player: self.status.setValue('移出，playerId=' + player),
        }, {'class': 'oreui:red_btn_thin'})
        self._button('订阅 / 取消订阅文本变化', self.toggleSubscription)
        form.divider({'class': 'oreui:divider_in'})
        form.divider({'class': 'oreui:divider_out'})
        form.group({
            'inner': {'children': {
                'caption': {'label': self.countText},
                'button': {'label': '嵌套 Group 按钮', 'callbacks': {'onClick': self.increment}},
            }},
            'menu': {'label': '组内下拉菜单', 'items': self.items, 'value': self.selected},
            'switch': {'label': '绑定同一个可见性变量', 'state': self.visible},
            'custom': {'params': {'text': self.text, 'palette': self.palette, 'history': self.history}},
        }, {'class': self.prefix + ':group', 'size': self.groupSize, 'offset': self.groupOffset})
        form.label('Group 内部按父组百分比布局。\n组内按钮、菜单、开关、Custom 共用状态。\n独立 offsetX/Y 覆盖注册时的 offset。', {'height': 218})
        self._button('改变 Group 尺寸与位移', self.changeGroup)
        self._button('替换列表 / 字典 Observable', self.changeContainers)
        form.custom({'text': self.text, 'palette': self.palette,
                     'history': self.history, 'sessionKey': self.key, 'appendOnCreate': True},
                    {'class': 'example:custom_label', 'height': 52})
        form.custom({'text': '另一个独立 Custom 实例', 'palette': {'color': [0.2, 0.8, 1.0]}},
                    {'class': 'example:custom_label', 'height': 52})
        self._button('调整根尺寸和偏移', self.changeRoot)
        self._button('根尺寸 / 偏移恢复 default', self.restoreRoot)
        self._button('显示后追加按钮和文本', self.appendControls)
        self._button('默认样式：追加放大文本', self.defaultStyle)
        self._button('重复 show（应报告 RuntimeError）', self.repeatShow)
        self._button('查询 isShowing(playerId)', self.queryShowing)
        self._button('第二张表单：覆盖并隐藏主表单', self.openPopup)
        self._button('关闭后重新显示同一个对象', self.closeAndReopen)
        self._button('close() 关闭本表单', self.close)
        self._button('Screen.closeAllForms() 关闭全部', self.closeAll)

    def increment(self, playerId):
        self.count.setValue(self.count.getValue() + 1)
        self.title.setValue('%s功能展台 / 点击 %s 次' % (
            '客户端' if self.side == 'client' else '服务端', self.count.getValue()))
        self.status.setValue('按钮回调 playerId=' + playerId)

    def changeRange(self, playerId):
        modes = [(0, 10, 1), (0, 10, 0), (10, -2, -2), (5, 5, 1), (0, 1, 0.1)]
        self.rangeIndex = (self.rangeIndex + 1) % len(modes)
        low, high, step = modes[self.rangeIndex]
        self.minimum.setValue(low)
        self.maximum.setValue(high)
        self.step.setValue(step)
        self.number.setValue(3.3)
        self.status.setValue('min=%s / max=%s / step=%s；原始值=3.3' % (low, high, step))

    def changeFont(self, playerId):
        self.fontIndex = (self.fontIndex + 1) % 3
        self.font.setValue((1.0, 1.5, 'default')[self.fontIndex])

    def toggleSubscription(self, playerId):
        if self.subscribed:
            self.text.unsubscribe(self.onText)
        else:
            self.text.subscribe(self.onText)
        self.subscribed = not self.subscribed
        self.status.setValue('文本订阅已' + ('开启' if self.subscribed else '取消'))

    def changeGroup(self, playerId):
        small = self.groupSize.getValue()[0] != '70%-8px'
        self.groupSize.setValue(['70%-8px' if small else '100%-8px', 238 if small else 218])
        self.groupOffset.setValue([12 if small else 4, 6 if small else 0])

    def changeContainers(self, playerId):
        # 列表 / 字典用新对象替换；原地 append 不会触发 Observable 通知。
        self.history.setValue(self.history.getValue() + ['第 %s 条' % len(self.history.getValue())])
        color = self.palette.getValue()['color']
        self.palette.setValue({'color': [0.05, 0.4, 0.65] if color == [0.2, 0.2, 0.2] else [0.2, 0.2, 0.2]})

    def changeRoot(self, playerId):
        self.rootWidth.setValue('82.5%y-2.25px')
        self.rootHeight.setValue('82%')
        self.rootX.setValue('-4.5px')
        self.rootY.setValue('2.5px')

    def restoreRoot(self, playerId):
        for value in (self.rootWidth, self.rootHeight, self.rootX, self.rootY):
            value.setValue('default')

    def appendControls(self, playerId):
        self.appended += 1
        self.form.label('动态追加 #%s；已有控件状态应保留。' % self.appended, {'height': 32})
        self._button('追加按钮 #%s' % self.appended, self.increment)
        self.report('控件已追加到表单底部，请向下滚动。')

    def defaultStyle(self, playerId):
        # 默认样式影响后续创建的控件，并跨端同步；本演示仅临时设置后恢复。
        Screen.setDefaultStyle('label', {'fontSize': 1.4})
        try:
            self.form.label('来自默认 fontSize=1.4 的新文本', {'height': 36})
        finally:
            Screen.setDefaultStyle('label', {})

    def queryShowing(self, playerId):
        self.report('isShowing(%s)=%s；isShowing()=%s' % (
            playerId, self.form.isShowing(playerId), self.form.isShowing()))

    def repeatShow(self, playerId):
        try:
            self.form.show(self.playerId)
        except RuntimeError as error:
            self.report('重复 show 正确被拒绝：%s' % error)
        else:
            self.report('异常：重复 show 没有报错，请检查。')

    def openPopup(self, playerId):
        popup = Form.create('第二张表单', {
            'class': 'oreui:dark_panel_thin', 'width': '72%y', 'height': '45%',
            'hideOtherForms': True, 'layer': 20,
        })
        popup.label('关闭后，主表单应恢复原来的输入和滚动状态。', {'height': 48})
        popup.button('关闭弹层', {'onClick': lambda player: popup.close(player)})
        self.popups.append(popup)
        def closed(args):
            self.popups.remove(popup)
            self.report('弹层已关闭，playerId=%s / reason=%s' % (args.playerId, args.closeReason))
        popup.show(self.playerId).onClose(closed)

    def show(self):
        if self.form.isShowing(self.playerId):
            self.report('该测试表单已显示；可使用表单内的重复 show 按钮测试报错。')
            return
        self.form.show(self.playerId).onClose(self._closed)
        self.showCount += 1
        if self.showCount == 1:
            self.form.label('show() 后立即追加：等待创建期间也应正常出现。', {'height': 32})

    def _closed(self, args):
        for callback in self.closedHooks:
            callback()
        self.report('表单关闭：playerId=%s / reason=%s / isShowing=%s' % (
            args.playerId, args.closeReason, self.form.isShowing(args.playerId)))
        if self.reopen:
            self.reopen = False
            # 服务端 close() 异步，等关闭回执再安排重开。
            self.schedule(self.show)

    def closeAndReopen(self, playerId):
        self.reopen = True
        self.form.close(self.playerId)

    def close(self, playerId):
        self.reopen = False
        self.form.close(self.playerId)

    def closeAll(self, playerId):
        self.reopen = False
        Screen.closeAllForms(self.playerId)
