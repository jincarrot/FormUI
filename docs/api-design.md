# 接口设计与推荐用法

本次检查覆盖库入口与自动注册、Form/Observable/Screen/Control 公共接口、客户端与服务端消息处理、Group/ListView 的创建与更新、三种风格注册、UI 资源及其生成脚本、示例和类型声明。改进以兼容现有调用、减少重复配置和提前暴露调用错误为原则。

## 推荐的表单写法

```python
# -*- coding: utf-8 -*-
from FormUI.lib import Form, Observable


def create_counter():
    count = Observable.create(0)
    status = count.map(lambda value: '当前计数：%s' % value)

    form = Form.create('计数器', {
        'width': '80%y', 'height': '70%',
    }, theme='fluent-dark')
    form.label(status)
    form.button('增加', lambda playerId: count.update(lambda value: value + 1))
    form.button('关闭', lambda playerId: form.close(playerId))
    return form, count


# 在系统和客户端 UI 就绪后，由业务对象保存并显示：
# self.form, self.count = create_counter()
# self.form.show()               # 客户端
# self.form.show(targetPlayerId) # 服务端
```

`Form.create(title, style=None, theme=None, grid=None, layout=None)` 支持五种内置主题以及 `Theme.register` 注册的自定义名称。内置主题包括 `oreui`、`flutter`、`flutter-dark`、`fluent`、`fluent-dark`，同时设置根面板以及 button、label、divider、toggle、slider、textfield、dropdown、listview 的默认 class。Flutter 的默认按钮是 FilledBtn，Fluent 是 PrimaryBtn，OreUI 是 NormalBtn。

每个属性的覆盖顺序为：内置默认值 → `Screen.setDefaultStyle` → 表单主题样式 → 调用时显式 style。内置主题只更改 class，自定义主题还可以覆盖高度等完整样式属性。主题快照只影响当前 Form，不修改全局配置；Group 和 Custom 继续使用各自明确注册的模板，Group 内部子控件也不会被外层主题重写。

省略 theme 时读取 `Screen.setDefaultTheme` 指定的默认主题；未设置时保留原有按 class 配置的用法，默认根为 `oreui:light_panel_thin`。单独指定根面板 `style['class']` 不会推断子控件主题。自定义主题、Screen 全局网格、表单/控件的 grid 参数及 Group 局部网格，详见[主题与 Grid 指南](themes-grid.md)。

## 按钮与关闭回调

只需处理点击时，可以直接传函数：

```python
form.button('保存', save)
# 等价于 form.button('保存', {'onClick': save})
```

`save(playerId)` 的参数保持不变。需要悬停等事件时继续传字典，支持 `onClick`、`onMoveIn`、`onMoveOut`。Group 实例子控件的 `callbacks` 字段也接受此简写。未知事件名、不可调用的回调会在添加控件时抛错，避免错误一直隐藏到点击阶段。

`show` 可直接接收关闭回调，在发送表单之前就完成绑定：

```python
form.show(playerId, onClose=lambda args: handle_close(args.playerId, args.closeReason))
```

返回值仍是 `FormShowResult`，旧的 `form.show(playerId).onClose(callback)` 继续可用。`result.onClose` 的返回值仍为 `None`，传 `None` 可以清除该显示结果的业务关闭回调。直接在 `show` 中传入回调，还能覆盖发送期间同步收到关闭事件的情况。

## 嵌入当前界面

`show(target=None, onClose=None, options=None)` 的 `options['combineUI']` 默认为 `False`，使用原有的 FormUI 页面。设为 `True` 时，每个目标客户端在收到显示请求时取得自己的栈顶 ScreenNode，并在该界面内创建表单。该选项只影响本次显示。

```python
# -*- coding: utf-8 -*-
from FormUI.lib import Form, Observable

def show_settings(playerId):
    enabled = Observable.create(True)
    form = Form.create('设置', theme='fluent-dark')
    form.toggle('显示提示', enabled)
    form.button('完成', lambda player: form.close(player))
    form.show(playerId, options={'combineUI': True})
    return form
```

上例在服务端显示给指定玩家。客户端写作 `form.show(options={'combineUI': True})`。按钮、输入、ListView、Observable 更新和显示后追加控件沿用原有接口。窗口的屏幕 Grid 以宿主画布为参照。多个表单挂在同一界面时，`hideOtherForms` 只影响该界面中的较早表单。

调用 `form.close(playerId)` 或点击表单自带的关闭按钮，只移除该表单的控件。宿主被其他界面覆盖时，仍可以按 Form 实例更新或关闭它。`Screen.closeAllForms()` 也会移除嵌入的表单。宿主自身关闭后，其附属表单随之关闭。

需要区分关闭原因时，可在显示时传入 `onClose`。

| `args.closeReason` | 触发时机 |
| --- | --- |
| `api` | 调用 `form.close()` 或 `Screen.closeAllForms()` |
| `user` | 点击表单关闭按钮，或表单所在的宿主界面关闭 |
| `unavailable` | 服务端请求嵌入，目标客户端无法取得宿主或创建控件 |

客户端本地调用时，如果没有可用的栈顶 ScreenNode，`show()` 抛出 `RuntimeError` 并撤销本次显示状态。服务端按玩家分别接收结果。

## Observable 更新、派生与订阅

| 方法 | 用法与返回值 |
| --- | --- |
| `getValue()` / `setValue(value)` | 保留原有读写方式；setValue 返回 None。 |
| `update(updater)` | updater 接收当前值的独立副本，必须返回新值；update 返回 None。 |
| `map(transform)` | 根据源 Observable 创建派生 Observable，初次立即计算，后续随源变化更新。 |
| `subscribe(callback)` / `unsubscribe(callback)` | 保留原有订阅方式，返回 None。 |
| `watch(callback, immediate=True)` | 返回可重复调用的取消函数；默认先通知一次当前值。 |

```python
count.update(lambda value: value + 1)
items.update(lambda rows: rows + [{'label': '新物品', 'value': 'new'}])
reversed_items = items.map(lambda rows: list(reversed(rows)))
message = count.map(lambda value: '计数：%s' % value)

stop = count.watch(on_count_changed)  # 立即执行一次，之后监听变化
stop()                              # 取消这次订阅
stop()                              # 重复取消无副作用
```

`update` 在回调重入时将计算操作排队，按执行时的最新已提交值计算，连续加一不会都基于同一个旧值。处理列表/字典时无需先手动复制容器；updater 抛错不会破坏原值。不要写 `items.update(lambda rows: rows.append(item))`，因为 append 返回 None；可以返回 `rows + [item]`，或在普通函数中修改副本后 `return rows`。

`map` 也传入数据副本，转换器应为无副作用的计算函数。派生值的业务写入应作用于源 Observable。建议在构建表单时创建并保存派生值，重开表单时复用，避免每次显示都创建新映射。现有管理器仍按会话保留 Form/Observable，当前未引入跨端自动销毁协议。

更新事件的旧约定保持不变：`subscribe` / `watch` 的变更回调参数是新值，回调期间 `getValue()` 仍返回旧值。相同值不重复通知。watch 的初次通知是当前值，不属于一次变更；传 `immediate=False` 可跳过。首次通知抛错时会自动取消本次订阅。

## 目标玩家和显示状态

服务端的 `show`、`close`、`Screen.closeAllForms` 统一接受单个玩家 ID 或可迭代的 ID 集合。列表、元组、生成器都只消费一次，去重时保留输入顺序。

| 服务端 target | 行为 |
| --- | --- |
| `'playerId'` | 指定玩家。 |
| `['p1', 'p2']` 或生成器 | 指定集合。 |
| `None` / 省略 | 当前全部在线玩家。 |
| `[]` / 空迭代器 | 不发送任何操作，不会扩大为全体玩家。 |
| 空字符串、数字、布尔值、字典、含非法 ID 的集合 | 在发送前抛出明确错误。 |

客户端仍只操作本地玩家，保留旧的 target 兼容行为。服务端群发属于显式业务选择，单玩家菜单应传 `playerId`。

```python
form.getShowingPlayers()  # 当前在线且正在显示/等待创建的玩家 ID 列表
form.isAnyShowing()      # 是否至少有一位在线玩家正在显示
form.isShowing(playerId) # 查询指定玩家
```

旧的 `isShowing()` 无参语义保持不变：客户端查询本地玩家，服务端要求历史显示过的全部玩家在线且仍显示。不要用它表示“至少一人正在显示”，请用 `isAnyShowing()`。服务端关闭依然等待客户端回执，立即 close 后不能假定已完成关闭。

## 配置所有权和注册诊断

- Form 控件参数、默认风格、注册选项保存独立的普通容器副本；修改调用者原来的字典/列表，不会悄悄改变已经添加的控件或全局配置。
- Observable 和函数保持原对象身份，复制配置不会复制出新的绑定。需要动态改变配置时使用 Observable。
- `Screen.getDefaultStyle(controlType)` 返回已配置默认值的副本；它不包含某个具体 Form 的主题或内置回退值。修改副本后需要调用 `setDefaultStyle` 才会生效。传入空字典可替换掉该类型已有的全局配置。
- 标准控件注册描述的路径列表互相独立。`Control.register` 收到不支持的描述类型时抛出 TypeError，onCreate/onObservableUpdate 非函数时也立即报错。
- 自动注册完成后会重新查询系统，修复首次查找仍返回注册前 None 的问题。导入 `FormUI.lib` 的自动注册机制保持不变；对象创建与 UI 显示仍需遵守原有初始化时机。
- 未找到的远端 Observable ID、按钮回调 ID会被忽略，避免无效引用导致消息处理崩溃。这不是业务权限校验，服务端业务仍应验证玩家的操作条件。

## 本次修复与兼容性

修复了 `close([])` 意外变为全体关闭、生成器目标被提前耗尽、重复目标重复发送、默认根面板为空、首次注册后系统查询过期、默认配置共享容器，以及数据包装函数共享默认记录列表的问题。

`Form.create` 原来的两个位置参数、所有控件方法的原有参数顺序、按钮字典回调、Observable 的 get/set 与订阅方法、显式 class 风格、显示结果与关闭回调类型均保持兼容。新增可选参数追加在原参数之后；旧调用中的非法回调、非法主题和非法目标会更早报错。

本地验证覆盖公开调用、数据流、资源引用、类型声明和旧示例回归。实际游戏里的鼠标/触摸滚动、初始化事件顺序和跨端网络时序仍需要加载行为包与资源包验收。ListView 的五种外观和服务端演示继续使用 [原聊天命令](listview.md#游戏内演示与检查)，其实现已采用新主题、按钮简写、map 和 update 接口。
