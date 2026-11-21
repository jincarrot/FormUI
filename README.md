# FormUI

一款适用于网易版《我的世界》的多功能表单库，支持自定义控件，布局，客户端/服务端通用。

此为先前[MoreUI](https://github.com/jincarrot/MoreUI)的升级，MoreUI已停止维护。

[接口设计与推荐用法：主题、简洁回调和 Observable 辅助方法](docs/api-design.md)

[自定义主题与 Grid：Screen 全局网格、窗口定位、控件跨格及 Group 局部布局](docs/themes-grid.md)

[客户端性能优化、调用次数对比和复测方法](docs/client-performance.md)

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

要把表单加进玩家当前打开的界面，客户端可调用 `form.show(options={'combineUI': True})`，服务端可调用 `form.show(playerId, options={'combineUI': True})`。嵌入后仍用 `form.close()` 或 `form.close(playerId)` 移除表单，宿主界面保持打开。[嵌入表单用法](docs/api-design.md#嵌入当前界面)

[custom 控件使用说明](docs/custom-controls.md)

[Group 控件使用说明](docs/group-controls.md)

[ListView 动态列表、三种风格及使用示例](docs/listview.md)

[布局与参数约定](docs/layout-parameters.md)

[使用 AI Skill 编写 FormUI 表单](docs/skill-usage.md)

[Flutter / Material 风格内置控件](docs/flutter-ui.md)

[Fluent Qt 窗口风格内置控件](docs/fluent-ui.md)

内置样式标识符可通过 `from FormUI.lib import InnerStyles` 使用，例如 `InnerStyles.flutter.FilledBtn`、`InnerStyles.fluent.PrimaryBtn`。也可独立导入 `FormUI.innerStyles`，获取 `InnerStyles`、`OreUIStyles`、`FlutterStyles` 和 `FluentStyles`。

[聊天触发的客户端 / 服务端功能测试与双正方形动画](docs/test-examples.md)
