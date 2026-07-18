# -*- coding: utf-8 -*-
import mod.server.extraServerApi as serverApi

ServerSystem = serverApi.GetServerSystemCls()
comp = serverApi.GetEngineCompFactory()
from MoreUI.lib import * # 服务端导入此即可使用MoreUI，记得在客户端导入MoreUI.register以注册

class ExampleServer(ServerSystem):

    def __init__(self, namespace, systemName):
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "ServerChatEvent", self, self.example)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), "OnScriptTickServer", self, self.onTick)
        self.tick = 0

    def onTick(self):
        self.tick += 1
        if self.tick % 60:
            return
        comp.CreateCommand(serverApi.GetLevelId()).SetCommand("title @s actionbar 输入MoreUI/CustomForm/Observable/Layout即可看到测试代码的效果！", serverApi.GetPlayerList()[0])

    def example(self, data):
        """MoreUI样例"""
        playerId = data['playerId']
        if data['message'] == 'MoreUI':
            self.MoreUIExample(playerId)
        elif data['message'] == 'CustomForm':
            self.CustomFormExample(playerId)
        elif data['message'] == 'Observable':
            self.ObservableExample(playerId)
        elif data['message'] == 'Layout':
            self.LayoutExample(playerId)
        elif data['message'] == 'ConfigMenu':
            self.ConfigMenuExample(playerId)
        elif data['message'] == 'SidebarForm':
            self.SidebarFormExample(playerId)

    def SidebarFormExample(self, playerId):
        """SidebarForm 样例：左侧图标标签，右侧显示对应表单"""
        sidebar = SidebarForm.create(playerId)

        home = CustomForm.create(playerId, "主页")
        home.label("欢迎使用 SidebarForm！")
        home.button("一个按钮", lambda: None)

        settings = CustomForm.create(playerId, "设置")
        settings.toggle("开关", Observable.create(False, {"clientWritable": True}))
        settings.slider("数值", Observable.create(5, {"clientWritable": True}), 0, 10)

        about = CustomForm.create(playerId, "关于")
        about.label("这是第三个标签页。")

        sidebar.tab("textures/ui/icon_setting", home)
        sidebar.tab("textures/ui/gear", settings)
        sidebar.tab("textures/ui/infobulb", about)
        sidebar.show()

    def ConfigMenuExample(self, playerId):
        menu = ConfigMenu.create(playerId, "测试配置")

        intro = CustomForm.create(playerId, "模组介绍")
        intro.label("你好你好\n\nxxxx\n\n再见再见")

        globalConfig = CustomForm.create(playerId, "全局设置")
        selection = Observable.create(1, {"clientWritable": True})
        configs = [
            {"label": "配置1", "value": 1},
            {"label": "配置2", "value": 2},
            {"label": "配置3", "value": 3}
        ]
        globalConfig.label("这个界面只是演示测试界面功能，没有实际意义！")
        globalConfig.divider()
        globalConfig.dropdown("选择一个配置", selection, configs)

        monster = CustomForm.create(playerId, "222")
        spawnRate = Observable.create(1, {"clientWritable": True})
        damageRate = Observable.create(1, {"clientWritable": True})

        monster.label("这个界面只是演示测试界面功能，没有实际意义！")
        monster.divider()
        monster.slider("刷怪速率", spawnRate, 0, 10)
        monster.slider("伤害倍率", damageRate, 0, 10)
        monster.toggle("启用变态模式", Observable.create(False, {"clientWritable": True}))
        monster.toggle("启用无敌模式", Observable.create(False, {"clientWritable": True}))

        menu.addPage(intro)
        menu.addPage(globalConfig)
        menu.addPage(monster, "怪物")
        menu.show()

    def MoreUIExample(self, playerId):
        ui = MoreUI.create(playerId)
        formData = ui.addCustomForm("测试界面1")
        formData.form.button("测试按钮", lambda: None)
        ui.show()

    def CustomFormExample(self, playerId):
        form = CustomForm.create(playerId, "测试表单1")
        form.button("测试按钮1", lambda: None)
        form.button("测试按钮2", lambda: None)
        form.divider()
        form.label("测试文本1")
        form.label("测试文本2")
        form.divider()
        form.show()

    def ObservableExample(self, playerId, show=True):
        title = Observable.create("我是标题", {"clientWritable": True})
        form = CustomForm.create(playerId, title)
        form.textField("输入文本，标题会随之改变", title)

        toggled = Observable.create(False, {"clientWritable": True})
        toggleTitle = Observable.create("点我显示更多控件！")
        @toggled.subscribe
        def switchToggle(value):
            op = 1 if value else 0
            texts = ["隐藏", '显示']
            toggleTitle.setData("点我%s更多控件！" % texts[op])
        form.toggle(toggleTitle, toggled)
        form.divider({"visible": toggled})

        items = [
            {
                "label": "More",
                "value": 1
            },
            {
                "label": "UI",
                "value": 3
            },
            {
                "label": "MoreUI",
                "value": 5
            }
        ]
        sliderValue = Observable.create(1, {"clientWritable": True})
        form.dropdown("我可以影响到滑动条！", sliderValue, items, {"visible": toggled})
        form.slider("滑动也可以改变下拉框的值！", sliderValue, 1, 5, {"visible": toggled})
        form.divider({"visible": toggled})

        if show:
            form.show()
        else:
            return form

    def LayoutExample(self, playerId):
        layout = {
            "column": [2, 3, 1, 1],
            "row": [1, 2, 2]
        }
        ui = MoreUI.create(playerId, layout)

        click = {"t": 0}
        buttonLabel = Observable.create("点我隐藏界面2！")
        form = self.ObservableExample(playerId, False)
        def btn1():
            click['t'] += 1
            if click['t'] % 2:
                buttonLabel.setData("点我显示界面2！")
                form2.close()
            else:
                buttonLabel.setData("点我隐藏界面2！")
                form2.show()
        offset1X = Observable.create(0, {"clientWritable": True})
        form.button(buttonLabel, btn1)
        ui.addForm(form, {"offset": [offset1X, 0], "position": [0, 0], "size": [1, 2]})

        resizable = Observable.create(False, {"clientWritable": True})
        @resizable.subscribe
        def switchToggle(value):
            if value:
                content.setData("现在我可以缩放啦！（点右下角）")
            else:
                content.setData("点我上面，可以移动我！")
        content = Observable.create("点我上面，可以移动我！")
        form2 = ui.addCustomForm("我是界面2!", {"movable": True, "resizable": resizable}, {"position": [2, 1], "size": [1, 1]}).form
        form2.label(content)

        form3 = ui.addCustomForm("我是界面3！", layout={"position": [0, 2], "size": [4, 1]}).form
        form3.slider("我可以滑动界面1！", offset1X, 0, 300)
        form3.toggle("我可以控制一点东西……", resizable)

        ui.show()
