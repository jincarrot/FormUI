# 表单、绑定和风格

以下导入以宿主可直接导入 `FormUI` 为前提，代码在系统和客户端 UI 就绪后的业务入口执行。路径及生命周期按宿主调整。

## 最小客户端设置表单

```python
# -*- coding: utf-8 -*-
from FormUI.lib import Form, Observable
from FormUI.innerStyles import InnerStyles


def create_settings():
    theme = InnerStyles.fluent
    name = Observable.create('Steve')
    enabled = Observable.create(True)
    volume = Observable.create(60)
    quality = Observable.create(1)
    form = Form.create('设置', {
        'class': theme.LightPanel,
        'width': '80%y', 'height': '80%', 'grids': [1],
    })
    form.label('个人设置', {'class': theme.Label, 'fontSize': 1.2})
    form.textfield('名称', name, {'class': theme.Textfield})
    form.toggle('启用音效', enabled, {'class': theme.Toggle})
    form.slider('音量', volume, 0, 100, 1, {'class': theme.Slider})
    form.dropdown('画质', [
        {'label': '流畅', 'value': 0},
        {'label': '均衡', 'value': 1},
        {'label': '精致', 'value': 2},
    ], quality, {'class': theme.Dropdown})
    form.button('完成', {'onClick': lambda playerId: form.close(playerId)},
                {'class': theme.PrimaryBtn})
    return form, {'name': name, 'enabled': enabled,
                  'volume': volume, 'quality': quality}


# 在业务对象中保留 form 和 state，避免每次点击重新创建状态。
# form, state = create_settings()
# if not form.isShowing():
#     form.show()
```

服务端也可构造同样的表单，但以 `form.show(playerId)` 指定玩家。不要在服务端执行原生 UI 回调或导入客户端专用业务模块。

## 公开调用参数

| 调用 | 主要参数 |
| --- | --- |
| `Form.create(title, style={})` | 标题可绑定 Observable；style 包含 class、宽高、偏移、grids、hideOtherForms、layer、visible |
| `button(label, callbacks={}, style={}, params={})` | callbacks 可含 onClick、onMoveIn、onMoveOut，均接收 playerId |
| `label(text, style={}, params={})` | fontSize 为缩放倍数，可绑定 Observable |
| `toggle(label, state, style={}, params={})` | state 使用布尔值或布尔 Observable |
| `slider(label, value, minValue=0.0, maxValue=1.0, step=1, style={}, params={})` | 值、边界、步长可绑定数值 Observable |
| `textfield(label, value, style={}, params={})` | 文本值可绑定 Observable |
| `dropdown(label, items, value, style={}, params={})` | items 为字符串 label、整数或字符串 value 的静态字典列表 |
| `divider(style={}, params={})` | 无文本和回调参数 |
| `group(children={}, style={}, params={})`、`custom(params={}, style={})` | 见 composition.md |

普通控件 style 使用 `class/offsetX/offsetY/width/height/visible`，Label 另外支持 `fontSize`。`offset/size` 二元素列表简写用于 Group，不推广到普通控件或 Form 根样式。

params 必须是字典，默认空字典；注册控件的客户端 `onCreate` 通过 args.params 读取当前实例的独立快照，嵌套 Observable 会解包为当前值。普通控件 params 用于初始化，不会触发 Custom 的 onObservableUpdate；也不会作为按钮点击回调的额外参数。业务数据优先通过 params 传入，style 仍用于布局。

## 状态所有权与回调

Observable 可以保存列表、字典及普通可传输值。替换容器使用 `setValue(新列表或字典)`；原地修改已有容器不会自动通知。`subscribe(callback)` 的参数是本次新值，回调期间 `getValue()` 仍是旧值；回调内再次 setValue 会排队。派生运算如 `count + 1` 返回新的 Observable，`bool(observable)` 才直接读取当前值。

不要把 `observable == value` 当普通布尔比较或拿它做对象身份判断：比较运算会产生派生 Observable。身份判断用 `is`，比较当前值用 `getValue()`。

创建 Observable 不等于在另一端创建可查询的同一个 Python 对象。显示表单时传输绑定编号和当前值；原始对象保存在创建端。服务端编号从 0 递增，客户端从 -1 递减，`-1` 是有效编号，业务代码无需自行管理编号。输入控件把更新送回对应编号的所属端；Custom 直接使用参数快照。

客户端 Observable 用于本地状态。多人共享状态通常由服务端创建并给不同玩家绑定同一个 Observable；要求玩家互不影响时为每位玩家创建独立状态及表单，不能无意复用一份共享对象。

## 显示与关闭

- 客户端 `show()` 只显示给本地玩家；服务端 `show(playerId)`、`show([playerId, ...])`、`show()` 分别针对指定玩家、列表、全部在线玩家。
- `isShowing(playerId)` 查询特定玩家。客户端省略参数查询本地玩家；服务端省略参数要求历史显示过的玩家全部在线且仍显示，未显示过返回 False，任一历史目标已关闭或离线也返回 False。
- `form.show(playerId).onClose(callback)` 中 callback 接收对象，`closeReason` 为 `api` 或 `user`；玩家离线清理状态但不调用关闭回调。onClose 返回 None，不能把结果当 Form 保存。
- `close()` 默认客户端关闭本地，服务端发给全部在线玩家；服务端单人关闭使用 `close(playerId)`。`Screen.closeAllForms(target)` 需要 target 参数，业务清理优先关闭自己拥有的表单。
- 可以在 show 后或 Custom.onCreate 中追加控件，库会创建并重排；不要为一次追加重复 show。
- 多表单同时显示参考 `example_styles.py`：先等首个 FormUI 页面完成创建，再显示后续表单；设置适当位移、尺寸及 `hideOtherForms=False`。不要假设连续首次 show 会自动落在同一页面上。

## 风格与布局

`InnerStyles.oreui/flutter/fluent` 和 `OreUIStyles/FlutterStyles/FluentStyles` 提供 class 常量，也从 lib 导出。Flutter 主按钮为 FilledBtn，Fluent 为 PrimaryBtn，OreUI 可用 NormalBtn/GreenBtn；OreUI 常量没有 Toggle，使用已注册的 `oreui:toggle_thin`。深色 Flutter/Fluent 子控件须显式使用 DarkLabel、DarkToggle 等，面板为 DarkPanel。

客户端 UI 初始化自动注册内置风格。Flutter/Fluent 面板居中；根偏移基于其锚点。不指定控件 class 时仍沿用默认配置中的 OreUI class。单张表单选择其他风格时逐项传 class；`Screen.setDefaultStyle(controlType, style)` 会跨端同步并改变后续创建的默认配置，只有需要全局效果时才使用。

`grids` 是非空有限正权重列表，如 `[1, 2]` 表示两列宽度比例；依添加顺序按行排列。Group 作为一个根控件占一个格子。下拉菜单展开覆盖后续控件，不挤开其他格子。

尺寸支持数字像素、`50%`、`50%-8px`、`72%y`、`default`、`fill`；百分比相对直接父控件，`%x/%y` 指定父宽/高，同一表达式不能混用参考轴。根尺寸或偏移设为 default 可恢复原生初始布局。

`fontSize` 是非负有限缩放倍数，不是像素字号。创建时 default 保留模板设置，运行时 default 恢复 1.0。滑动条 step=0 为连续模式，负步长取绝对值，反向边界自动排序，超范围展示值钳制；边界更新不主动改写 Observable 原值。详细规则读项目 `docs/layout-parameters.md`。
