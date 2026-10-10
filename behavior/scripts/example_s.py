# -*- coding: utf-8 -*-
"""服务端测试入口：监听 ServerChatEvent，仅响应 fui 前缀的聊天消息。"""
import mod.server.extraServerApi as serverApi
from FormUI.lib import *
from .example_shared import DemoSession, register_groups

ServerSystem = serverApi.GetServerSystemCls()


class ExampleServer(ServerSystem):
    def __init__(self, namespace, systemName):
        ServerSystem.__init__(self, namespace, systemName)
        self.sessions = {}
        self.shared = None
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(),
                            'ServerChatEvent', self, self.onChat)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(),
                            'PlayerLeftMessageServerEvent', self, self.onPlayerLeft)
        self.ListenForEvent('FormUIExample', 'ExampleClient', 'clientDemoFeedback', self, self.onClientFeedback)
        # 不传 onCreate/onObservableUpdate；先于玩家 UI 初始化注册，以测试注册补发。
        Control.register('example:server_label', 'fui_ore_base.label', Label())
        register_groups('example_server')

    def report(self, playerId, message):
        serverApi.GetEngineCompFactory().CreateMsg(playerId).NotifyOneMessage(playerId, message)

    def schedule(self, callback):
        serverApi.GetEngineCompFactory().CreateGame(serverApi.GetLevelId()).AddTimer(0.1, callback)

    def onClientFeedback(self, data):
        playerId = data.get('playerId')
        if playerId in serverApi.GetPlayerList():
            self.report(playerId, data.get('message', ''))

    def onPlayerLeft(self, data):
        self.sessions.pop(data['id'], None)

    def onChat(self, data):
        words = data.get('message', '').strip().lower().split()
        if not words or words[0] != 'fui':
            return
        data['cancel'] = True
        playerId = data['playerId']
        command = words[1] if len(words) == 2 else 'help'
        if command in ('client', 'animation', 'cancel-client', 'flutter', 'flutter-dark', 'fluent', 'fluent-dark', 'compare'):
            self.NotifyToClient(playerId, 'runClientDemo', {
                'action': {'client': 'show', 'animation': 'animation', 'cancel-client': 'cancel',
                           'flutter': 'flutter', 'flutter-dark': 'flutter-dark',
                           'fluent': 'fluent', 'fluent-dark': 'fluent-dark', 'compare': 'compare'}[command],
            })
        elif command == 'server':
            session = self.sessions.get(playerId)
            if session is None:
                session = DemoSession('server', playerId,
                                      lambda text: self.report(playerId, '[服务端] ' + text), self.schedule)
                session.form.label('此 Label 在服务端注册，无原生回调。',
                                   {'class': 'example:server_label', 'height': 32})
                self.sessions[playerId] = session
            session.show()
        elif command == 'cancel-server':
            form = Form.create('服务端创建期间取消', {'class': 'oreui:light_panel_thin'})
            form.label('show 和 close 连续发送；不应留下空界面。')
            form.show(playerId).onClose(lambda args: self.report(
                args.playerId, '服务端取消创建回执：%s' % args.closeReason))
            form.close(playerId)
        elif command == 'close':
            session = self.sessions.get(playerId)
            if session:
                session.reopen = False
            Screen.closeAllForms(playerId)
            self.NotifyToClient(playerId, 'runClientDemo', {'action': 'close'})
        elif command == 'shared':
            self.showShared(playerId, False)
        elif command == 'all':
            self.showShared(playerId, True)
        else:
            self.report(playerId, '聊天输入（不带 /）：fui client | server | animation | shared | all | '
                        'flutter | flutter-dark | fluent | fluent-dark | compare | cancel-client | cancel-server | close | help')

    def showShared(self, requester, allPlayers):
        # 同一表单对象向不同玩家显示，状态、按钮计数由服务端统一维护。
        if self.shared is None:
            count = Observable.create(0)
            text = Observable.create('共享计数：0')
            count.subscribe(lambda new: text.setValue('共享计数：%s' % new))
            form = Form.create('服务端共享表单', {
                'class': 'oreui:light_panel_thin', 'width': '72%y', 'height': '55%',
            })
            form.label('任意玩家点击，所有显示此表单的玩家一起更新。', {'height': 48})
            form.label(text, {'height': 32})
            form.button('共享计数 +1', {'onClick': lambda player: count.setValue(count.getValue() + 1)})
            form.button('查询历史玩家是否全部显示', {'onClick': lambda player: self.report(
                player, '本玩家=%s；历史显示过的玩家全部显示=%s' % (form.isShowing(player), form.isShowing()))})
            form.button('只关闭自己的表单', {'onClick': lambda player: form.close(player)})
            self.shared = form
        players = serverApi.GetPlayerList() if allPlayers else [requester]
        targets = [player for player in players if not self.shared.isShowing(player)]
        if not targets:
            self.report(requester, '目标玩家均已显示共享表单。')
            return
        # all 展示列表 target；shared 展示单个玩家 target。
        target = targets if allPlayers else targets[0]
        self.shared.show(target).onClose(lambda args: self.report(
            args.playerId, '共享表单关闭：%s' % args.closeReason))
