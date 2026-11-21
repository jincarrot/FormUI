# 从 Python 表单生成 JSON UI 控件

结构固定、数据经常变化的表单可以在开发时生成 JSON UI。游戏加载资源包时读取控件定义，`show()` 使用原生模板创建节点，再将本次表单的文字、输入值、Observable 和回调绑定到对应节点。客户端和服务端可以共用同一个模板。

## 从已有表单生成

项目自带的 OreUI 物品列表包含 10 个表单控件和 30 个初始行。在仓库根目录运行以下命令即可从工厂函数生成资源。

```console
python tools/compile_form.py behavior/scripts/example_listview.py create_listview_form fui_generated_examples.item_list --resource-pack resource
```

三个位置参数分别是 Python 文件、文件中的函数名或 Form 变量名、公开的 JSON UI 控件名。控件名采用 `命名空间.控件名` 的形式，每部分使用英文字母、数字和下划线，首字符为字母或下划线。

该命令写入 `resource/ui/formui_generated/fui_generated_examples/item_list.json`，并将相对路径加入该资源包的 `ui/_ui_defs.json`。修改结构后可用同一命令重新生成。项目已附带这份资源。[表单源码](../behavior/scripts/example_listview.py) · [生成的 JSON UI](../resource/ui/formui_generated/fui_generated_examples/item_list.json)

工具使用桌面 Python 3，导入指定模块并调用工厂。工厂可直接返回 Form，也可将一个 Form 和其他状态一同放在元组或列表中返回。可选的 `--args` 接收 JSON 数组，`--kwargs` 接收 JSON 对象。需要自定义主题、Group 或 Custom 时，在工厂或其导入的模块中执行与游戏端相同的注册。目标资源包还需包含这些注册引用的原生模板和贴图。

## 在游戏中使用

假设 `settings_ui.py` 中有以下工厂。

```python
# -*- coding: utf-8 -*-
from FormUI.lib import Form, Observable


def create_settings(enabled_by_default=True):
    enabled = Observable.create(enabled_by_default)
    form = Form.create('设置', theme='fluent-dark')
    form.toggle('显示提示', enabled)
    form.label(enabled.map(lambda value: '提示已开启' if value else '提示已关闭'))
    form.button('完成', lambda player: form.close(player))
    return form.bindTemplate('my_forms.settings')
```

```console
python tools/compile_form.py settings_ui.py create_settings my_forms.settings --resource-pack resource
```

在服务端可以这样显示给一个玩家。

```python
form = create_settings(False)
form.show(playerId)
```

在客户端可以嵌入当前界面。

```python
form = create_settings()
form.show(options={'combineUI': True})
```

`bindTemplate(name)` 返回当前 Form，并记录调用时已有的控件。将它放在固定控件定义之后。之后仍可调用 `form.label(...)`、`form.button(...)` 等方法，FormUI 会动态创建新增部分。绑定不影响已打开的实例。`form.bindTemplate(None)` 让下次显示使用动态创建。

## 模板保存的内容

| 内容 | 处理时机 |
| --- | --- |
| 面板、各控件的原生模板、Group 子节点 | 导出时写入 JSON UI，显示时按实例绑定 |
| ListView 行 | 按导出时的数量预建，显示时填入当前条目。可观察列表更新后复用现有行，按数量差额增删 |
| 标题、文字、选中值、输入值、按钮和 Custom 回调 | 取自本次 Python 实例。两位玩家可显示不同内容、执行不同回调 |
| Grid、窗口尺寸、内容滚动范围 | 由原有布局逻辑按实际屏幕和视口计算 |
| Dropdown 菜单选项 | 匹配选项数量和行模板时，整个菜单的行通过一次原生创建装入已有菜单面板。数量不同的菜单仍可动态创建 |
| 绑定后新增的控件 | 在客户端按需创建 |

带版本的结构标识覆盖窗口模板、控件顺序、原生类型与 Group 子节点。客户端在调用业务回调前检查生成标记及全部预建节点。资源缺失、结构变更或资源包版本落后时，本次显示会回退到动态创建，并在客户端日志中给出原因。修改文字、选择值或回调可继续使用现有资源。切换到使用不同原生控件的主题时，可为该主题生成独立的模板名。

内置窗口通过 `$formui_content` 将预建控件放入自己的滚动内容。自定义滚动面板也可以使用这个变量。对于已有的固定滚动容器，FormUI 会在其内容区挂载生成的子树。布局和回调由 FormUI 绑定，业务侧继续调用 `show`、`close` 和原来的控件接口。

## 从已有 Form 对象导出

需要游戏 API 才能构造的表单，可以在客户端 UI 和相关控件注册就绪后调用 `form.toJsonUI('my_forms.settings')`。该方法返回可用 `json.dumps` 序列化的字典。手工保存时，将 JSON 写入资源包的 `ui/` 目录，并把相对路径加入 `ui/_ui_defs.json`。以相同名称导出已绑定的表单时，只导出绑定时记录的固定部分。
