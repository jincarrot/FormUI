# FormUI

一款适用于网易版《我的世界》的多功能表单库，支持自定义控件，布局，客户端/服务端通用。

此为先前[MoreUI](https://github.com/jincarrot/MoreUI)的升级，MoreUI已停止维护。

[旧版 MoreUI 迁移、导入与使用方法](docs/moreui-compat.md)

[接口设计与推荐用法：主题、简洁回调和 Observable 辅助方法](docs/api-design.md)

[自定义主题与 Grid：Screen 全局网格、窗口定位、控件跨格及 Group 局部布局](docs/themes-grid.md)

[客户端性能优化、调用次数对比和复测方法](docs/client-performance.md)

[从 Python 表单生成 JSON UI 控件，并用 bindTemplate 绑定](docs/compiled-forms.md)

```python
from FormUI.lib import Form, Observable

# 在系统和客户端 UI 就绪后创建、显示。
count = Observable.create(0)
form = Form.create('计数器', theme='fluent-dark')
form.label(count.map(lambda value: '计数：%s' % value))
form.button('增加', lambda playerId: count.update(lambda value: value + 1))
form.button('关闭', lambda playerId: form.close(playerId))
form.show()  # 服务端单玩家表单请传入 playerId
```

要把表单加进玩家当前打开的界面，在创建时传入 `layout={'combineUI': True}`。客户端使用 `form.show()`，服务端使用 `form.show(playerId)`。调用 `close` 只移除该表单的控件。[嵌入表单用法](docs/api-design.md#嵌入当前界面)

HUD 或固定卡片可用 `Form.create(root='fui:panel')` 创建透明底板。[固定面板与自定义底板](docs/api-design.md#选择表单根面板)

[custom 控件使用说明](docs/custom-controls.md)

[Group 控件使用说明](docs/group-controls.md)

[ListView 动态列表、三种风格及使用示例](docs/listview.md)

[布局与参数约定](docs/layout-parameters.md)

[使用 AI Skill 编写 FormUI 表单](docs/skill-usage.md)

[Flutter / Material 风格内置控件](docs/flutter-ui.md)

[Fluent Qt 窗口风格内置控件](docs/fluent-ui.md)

内置样式标识符可通过 `from FormUI.lib import InnerStyles` 使用，例如 `InnerStyles.flutter.FilledBtn`、`InnerStyles.fluent.PrimaryBtn`。也可独立导入 `FormUI.innerStyles`，获取 `InnerStyles`、`OreUIStyles`、`FlutterStyles` 和 `FluentStyles`。

[游戏内测试：攻击实体打开表单，查看 Observable 驱动的强度条和备注回显](docs/test-examples.md)
