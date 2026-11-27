# ListView 列表控件

ListView 是固定视口高度、内部纵向滚动的单选列表，适合物品选择、玩家菜单、任务目录和设置选项。OreUI、Flutter、Fluent 均提供内置模板；Flutter 和 Fluent 另有深色版本。模板随客户端 `UiInitFinished` 自动注册。

可以用 `Form.create('标题', theme='fluent-dark')` 自动为面板和 ListView 选择对应风格，省去逐个传 class。下方显式 class 示例仍可使用；新的主题、按钮回调简写和 Observable 辅助方法见 [接口设计与推荐用法](api-design.md)。

## 接入与签名

```python
form.listview(label, items, value=None, style={}, params={})
```

返回当前 Form，支持链式添加。客户端、服务端均可构建；客户端 `form.show()`，服务端 `form.show(playerId)`。应在 FormUI 系统就绪后创建对象，在客户端 UI 初始化完成后显示。宿主需要合并 `ui/_ui_defs.json` 中的三个新增文件：

- `ui/oreui_listviews.json`
- `ui/flutter_listviews.json`
- `ui/fluent_listviews.json`

这些文件引用既有风格的滚动条、行模板所需纹理以及 `fui.w`；保留已有 FormUI UI 文件与纹理资源。嵌入其他 Mod 时不需要携带演示脚本。

| 参数 | 说明 |
| --- | --- |
| `label` | 标题字符串或字符串 Observable；传空字符串隐藏文字，保留标题区域。 |
| `items` | `[{ 'label': '显示文字', 'value': '唯一标识' }, ...]` 或保存这种列表的 Observable。 |
| `value` | 当前选中标识或 Observable；`None` 表示未选择。 |
| `style` | 通用布局属性，加 `itemHeight` 和 `emptyText`。 |
| `params` | 标准控件实例参数，供自定义模板的客户端 `onCreate` 使用。 |

每行只接收 `label`、`value`。`label` 是普通字符串，`value` 是唯一的整数或字符串，不能使用布尔值。行内字段不能再嵌套 Observable；更新文字、顺序或条目数量时替换整个 `items` Observable 的值。空列表合法。

## 最小可用示例

以下函数在业务系统的 UI 就绪入口后调用。示例按库可直接导入 `FormUI` 编写；宿主实际使用 `scripts.FormUI` 时同步调整前缀。

```python
# -*- coding: utf-8 -*-
from FormUI.lib import Form, Observable
from FormUI.innerStyles import InnerStyles


def create_inventory_form():
    theme = InnerStyles.fluent
    items = Observable.create([
        {'label': '苹果', 'value': 'apple'},
        {'label': '钻石', 'value': 'diamond'},
        {'label': '铁锭', 'value': 'iron'},
    ])
    selected = Observable.create(None)
    message = Observable.create('请选择物品')
    # 回调参数就是新值；回调期间 getValue() 仍返回旧值。
    selected.subscribe(lambda new: message.setValue(
        '请选择物品' if new is None else '当前选择：%s' % new))

    form = Form.create('背包', {
        'class': theme.LightPanel,
        'width': '80%y', 'height': '80%', 'grids': [1],
    })
    form.listview('物品列表', items, selected, {
        'class': theme.ListView,
        'height': 180, 'itemHeight': 32, 'emptyText': '背包为空',
    })
    form.label(message, {'class': theme.Label, 'height': 28})
    form.button('清除选择', {
        'onClick': lambda playerId: selected.setValue(None),
    }, {'class': theme.PrimaryBtn})
    form.button('关闭', {
        'onClick': lambda playerId: form.close(playerId),
    }, {'class': theme.PrimaryBtn})
    return form, items, selected


# 在业务对象中保留这些对象；同一个玩家显示期间不能重复 show。
# self.form, self.items, self.selected = create_inventory_form()
# self.form.show()          # 客户端
# self.form.show(playerId)  # 服务端
```

## 刷新与选择规则

```python
items.setValue([
    {'label': '苹果 × 12', 'value': 'apple'},
    {'label': '钻石 × 3', 'value': 'diamond'},
])
selected.setValue('diamond')  # 程序选择
selected.setValue(None)       # 清除选择
items.setValue([])            # 显示 emptyText
```

- 点击行会更新视觉标记，并把选中值写回其 Observable。重复点击已经选中的行不产生新的值变更。
- `selected.subscribe(callback)` 接收新值，不接收玩家 ID。服务端为每位玩家单独创建表单与状态，并在回调中捕获对应 `playerId`，即可处理独立业务。复用同一个服务端 Observable 会让所有绑定它的玩家共享选择。
- `value` 传普通值或省略时仍可点击，但选择仅保存在当前客户端界面；业务需要读取结果时必须使用 Observable。
- 列表按 `value` 匹配选择，重排或改名后仍能保持选中标记。被选中的项删除后，不显示选中标记，原 Observable 值保持不变；需要业务同时清空时显式调用 `selected.setValue(None)`。重新加入同一标识会重新显示选中标记。
- 动态表单在 `items` 更新时重建行。使用预编译模板时，列表会复用已有行，并为当前位置绑定新的选项和点击回调。仅更新 `value` 时只刷新选中标记。替换数据时滚动位置可能变化。
- 两种方式都为当前数据保留完整的原生行集合。大量数据可在业务层搜索、筛选或分页。项目自带的 OreUI 示例使用了预建的 30 行。[生成与绑定列表模板](compiled-forms.md)

## 布局与风格

| `style` 属性 | 默认值 | 说明 |
| --- | --- | --- |
| `class` | `oreui:listview` | 传入 Form 的 theme 时使用对应主题；只指定面板 class 不会自动改变列表。 |
| `width` | `100%-8px` | 相对父布局，可绑定 Observable。 |
| `height` | `160` | 整个列表含标题的高度；应留出至少标题和内容边距所需的 32 像素，并再留出可见行空间。 |
| `itemHeight` | `32` | 每行高度，有限正数像素，可绑定数值 Observable。 |
| `emptyText` | `暂无内容` | 空列表提示，可绑定字符串 Observable。 |
| `offsetX` / `offsetY` | `4` / `0` | 通用偏移。 |
| `visible` | `True` | 通用显隐属性，可绑定 Observable。 |

ListView 在 Form 的 `grids` 中占一个格子，数据量增加只延长内部滚动内容，不把下方控件推远。内部滚动沿用当前库的原生滚动面板，包含鼠标和触摸两种路径。

| 风格 | 标识常量 | 外观 |
| --- | --- | --- |
| OreUI | `InnerStyles.oreui.ListView` | 深灰方形行、绿色选中条。 |
| Flutter 浅色 | `InnerStyles.flutter.ListView` | Material 圆角行、紫色选中条。 |
| Flutter 深色 | `InnerStyles.flutter.DarkListView` | 深色背景、浅紫选中条。 |
| Fluent 浅色 | `InnerStyles.fluent.ListView` | 浅色列表、悬停反馈、蓝色选中条。 |
| Fluent 深色 | `InnerStyles.fluent.DarkListView` | 深色列表、浅蓝选中条。 |

`ControlType.ListView` 的值为 `'listview'`，可用于 `Screen.setDefaultStyle` 设置后续列表的全局默认风格。

## 组合控件与自定义模板

ListView 可以作为 Group 子控件；注册定义提供 `class` 和布局，实例数据提供 `label/items/value`。Group 的标准布局只包含通用尺寸、偏移、显隐，因此内嵌 ListView 使用默认行高和空提示。

```python
from FormUI.lib import Control, Group

# 在客户端内置模板注册完成后执行。
Control.register('inventory:picker', 'fui.group', Group({
    'list': {'class': InnerStyles.fluent.ListView, 'size': ['100%', '100%']},
}))
form.group({'list': {
    'label': '物品', 'items': items, 'value': selected,
}}, {'class': 'inventory:picker', 'height': 180})
```

客户端自定义模板可使用 `Control.register(identifier, templatePath, ListView(...))`。`ListView` 注册描述提供 `scrollingPanelPath`、`labelPaths`、`emptyLabelPath`、`itemControl`、`itemButtonPath`、`itemLabelPaths`、`selectedPath`；默认路径分别为 `/content`、`('/label',)`、`/empty`、空字符串（必须配置）、空字符串（行根是按钮）、`('/button_label',)`、`/selected`。滚动面板内部需符合现有 `getScrollingContent` 路径约定，行模板的选中标记应支持 `SetVisible`。

## 资源和构建示例

导出工具附带一个含 30 个初始条目的构建函数，演示 Observable 筛选、重排、清空列表和设置选中项。生成的 OreUI 控件可随资源包交付。[构建函数](../tools/examples/listview_form.py) · [生成方法](compiled-forms.md)

维护 UI 资源时，可运行 `python -S -B tools/generate_listview_ui.py` 重新生成这三个文件。生成器复用已有风格的行视觉与滚动条；更新 Flutter/Fluent 原始风格资源后再运行该命令。
