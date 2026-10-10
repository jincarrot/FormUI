# -*- coding: utf-8 -*-
"""客户端测试入口：在聊天栏发送 fui client 或 fui animation。"""
import math
import mod.client.extraClientApi as clientApi
from FormUI.lib import *
from .example_shared import DemoSession, register_groups
from .example_flutter import create_flutter_form
from .example_fluent import create_fluent_form
from .example_styles import StyleComparison

ClientSystem = clientApi.GetClientSystemCls()


def square_sizes(angle, outerSide):
    """两框同心：轴对齐内框的四顶点始终落在旋转外框的边上。"""
    radians = math.radians(float(angle) % 360.0)
    innerSide = outerSide / (abs(math.cos(radians)) + abs(math.sin(radians)))
    return outerSide, innerSide


class ExampleClient(ClientSystem):
    def __init__(self, namespace, systemName):
        ClientSystem.__init__(self, namespace, systemName)
        self.session = None
        self.animation = None
        self.motionInstances = {}
        self.flutterForms = {}
        self.fluentForms = {}
        self.styleComparison = None
        self.ready = False
        self.pending = []
        self.ListenForEvent('FormUIExample', 'ExampleServer', 'runClientDemo', self, self.onCommand)
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(),
                            'UiInitFinished', self, self.onUiReady)

    def report(self, message):
        self.NotifyToServer('clientDemoFeedback', {
            'playerId': clientApi.GetLocalPlayerId(), 'message': '[客户端] ' + message,
        })

    def schedule(self, callback):
        game = clientApi.GetEngineCompFactory().CreateGame(clientApi.GetLevelId())
        game.AddTimer(0.1, callback)

    def onUiReady(self, data):
        # 推迟到初始化事件处理完成，确保内置 OreUI 和 Screen 已注册。
        def flush():
            self.ready = True
            pending, self.pending = self.pending, []
            for command in pending:
                self.onCommand(command)
        self.schedule(flush)
        # 原生回调只在客户端注册；服务端也可使用这个标识符创建 custom 实例。
        Control.register('example:custom_label', 'fui_examples.custom_label', Custom(
            onCreate=self.onLabelCreate, onObservableUpdate=self.onLabelUpdate))
        Control.register('example:squares', 'fui_examples.squares', Custom(
            onCreate=self.onSquaresCreate, onObservableUpdate=self.onSquaresUpdate))
        register_groups('example_client')

    def onCommand(self, data):
        if not self.ready:
            self.pending.append(dict(data))
            return
        action = data.get('action', 'show')
        if action == 'close':
            if self.session:
                self.session.close(clientApi.GetLocalPlayerId())
            if self.animation:
                self.animation['form'].close()
            for form in self.flutterForms.values():
                if form.isShowing():
                    form.close()
            for form in self.fluentForms.values():
                if form.isShowing():
                    form.close()
            if self.styleComparison:
                self.styleComparison.close()
            return
        if action == 'compare':
            if self.styleComparison is None:
                self.styleComparison = StyleComparison(self.schedule)
            if not self.styleComparison.show():
                self.report('三种风格的对比表单正在显示或已经全部显示。')
            return
        if action in ('fluent', 'fluent-dark'):
            form = self.fluentForms.get(action)
            if form is None:
                form = create_fluent_form(action == 'fluent-dark')
                self.fluentForms[action] = form
            if form.isShowing():
                self.report('Fluent 风格预览已经显示。')
            else:
                form.show()
            return
        if action in ('flutter', 'flutter-dark'):
            form = self.flutterForms.get(action)
            if form is None:
                form = create_flutter_form(action == 'flutter-dark')
                self.flutterForms[action] = form
            if form.isShowing():
                self.report('Flutter 风格预览已经显示。')
            else:
                form.show()
            return
        if action == 'animation':
            self.showAnimation()
            return
        if action == 'cancel':
            self.cancelCreation()
            return
        if self.session is None:
            self.session = DemoSession('client', clientApi.GetLocalPlayerId(), self.report, self.schedule)
            self.addAnimation(self.session.form, 'client-showcase')
            self.session.closedHooks.append(lambda: self.forgetMotion('client-showcase'))
        self.session.show()

    def onLabelCreate(self, args):
        self.renderLabel(args.control, args.params)
        if (self.session and args.params.get('appendOnCreate') and
                args.params.get('sessionKey') == self.session.key and not self.session.createdAppend):
            self.session.createdAppend = True
            # 真正在原生 onCreate 期间调用公开接口追加控件。
            self.session.form.label('Custom.onCreate 中追加成功。', {'height': 32})

    def onLabelUpdate(self, args):
        self.renderLabel(args.control, args.params)
        args.control.GetChildByPath('/detail').asLabel().SetText(
            '%s：%s -> %s' % (args.key, args.oldValue, args.newValue))

    def renderLabel(self, control, params):
        control.GetChildByPath('/label').asLabel().SetText(params.get('text', ''))
        history = params.get('history', [])
        if isinstance(history, (list, tuple)):
            detail = '列表长度：%s' % len(history)
        else:
            detail = 'history 类型异常：%s（应为列表）' % type(history).__name__
            source = self.session.history if self.session else None
            print('[FormUIExample] custom_label invalid history: path=%r, params=%r, '
                  'sourceId=%r, sourceValue=%r' % (
                      control.GetPath(), params,
                      source._id if source is not None else None,
                      source.getValue() if source is not None else None))
        control.GetChildByPath('/detail').asLabel().SetText(detail)
        color = params.get('palette', {}).get('color', [0.2, 0.2, 0.2])
        control.GetChildByPath('/label').asLabel().SetTextColor(tuple(color))

    def addAnimation(self, form, key):
        angle = Observable.create(0.0)
        running = Observable.create(False)
        state = {'form': form, 'angle': angle, 'running': running}
        if key == 'standalone':
            self.animation = state
        else:
            self.showcaseMotion = state
        form.custom({'instanceKey': key, 'angle': angle, 'running': running},
                    {'class': 'example:squares', 'height': 224})
        form.label('蓝框旋转，橙框只缩放。\n橙框顶点始终落在蓝框边上。\n图内按钮开始 / 暂停。\n滑动条也可以控制角度。', {'height': 224})
        form.slider('角度 Observable：0..360°', angle, 0, 360, 0)
        form.toggle('运行 Observable（与图内按钮联动）', running)
        form.button('角度归零并暂停', {'onClick': lambda player: self.resetMotion(state)})
        form.button('角度设为 45° 并暂停', {'onClick': lambda player: self.resetMotion(state, 45.0)})
        return state

    def resetMotion(self, state, angle=0.0):
        state['running'].setValue(False)
        state['angle'].setValue(angle)

    def motionState(self, key):
        return self.animation if key == 'standalone' else self.showcaseMotion

    def onSquaresCreate(self, args):
        key = args.params['instanceKey']
        state = self.motionState(key)
        token = {'control': args.control, 'params': dict(args.params)}
        self.motionInstances[key] = token
        self.renderSquares(token)
        button = args.control.GetChildByPath('/play/button').asButton()
        button.AddTouchEventParams()
        button.SetButtonTouchUpCallback(
            lambda data: state['running'].setValue(not state['running'].getValue()))

        # addRepeatFunc 由当前 FormUI Screen.Update 每帧执行；一次只排下一帧。
        # token 使旧实例的待执行回调在关闭 / 重开后失效。
        def frame():
            if self.motionInstances.get(key) is not token:
                return
            if state['running'].getValue():
                state['angle'].setValue((float(state['angle'].getValue()) + 2.0) % 360.0)
            self.renderSquares(token)
            args.screenNode.addRepeatFunc(frame, 1)
        args.screenNode.addRepeatFunc(frame, 1)

    def onSquaresUpdate(self, args):
        token = self.motionInstances.get(args.params['instanceKey'])
        if token is not None and token['control'].GetPath() == args.control.GetPath():
            token['params'] = dict(args.params)
            self.renderSquares(token)

    def renderSquares(self, token):
        control, params = token['control'], token['params']
        canvas = control.GetChildByPath('/canvas')
        width, height = canvas.GetSize()
        outerSide, innerSide = square_sizes(params.get('angle', 0), max(0.0, min(width, height) * 0.66))
        rotating = canvas.GetChildByPath('/rotating').asImage()
        fixed = canvas.GetChildByPath('/fixed').asImage()
        rotating.SetSize((outerSide, outerSide))
        rotating.Rotate(float(params.get('angle', 0)))
        fixed.SetSize((innerSide, innerSide))
        fixed.Rotate(0.0)
        control.GetChildByPath('/angle').asLabel().SetText(
            '%.1f° / 内框边长 %.1f' % (params.get('angle', 0), innerSide))
        text = '暂停' if params.get('running') else '开始'
        for name in ('default', 'hover', 'pressed'):
            control.GetChildByPath('/play/button/' + name + '/label').asLabel().SetText(text)

    def forgetMotion(self, key):
        self.motionInstances.pop(key, None)
        self.motionState(key)['running'].setValue(False)

    def showAnimation(self):
        if self.animation is None:
            form = Form.create('双正方形动画', {
                'class': 'oreui:light_panel_thin', 'width': '90%y', 'height': '85%', 'grids': [1, 1],
            })
            self.addAnimation(form, 'standalone')
            form.button('关闭', {'onClick': lambda player: form.close()})
        form = self.animation['form']
        if form.isShowing():
            self.report('动画表单已经显示。')
            return
        def closed(args):
            self.forgetMotion('standalone')
            self.report('动画已关闭：%s' % args.closeReason)
        form.show().onClose(closed)

    def cancelCreation(self):
        form = Form.create('创建期间取消（不应残留）', {'class': 'oreui:light_panel_thin'})
        form.label('不应该最终出现在界面上。')
        form.show().onClose(lambda args: self.report('取消创建回执：%s' % args.closeReason))
        form.close()

    def Destroy(self):
        self.motionInstances.clear()
        self.pending = []
