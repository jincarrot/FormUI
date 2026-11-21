# 自定义主题与 Grid 布局

代码在 FormUI 系统及客户端 UI 就绪后执行，沿用宿主自己的导入前缀。客户端显示用 `form.show()`，服务端显示给指定玩家用 `form.show(playerId)`。运行时保持 Python 2.7 兼容。

## 一个完整例子

```python
# -*- coding: utf-8 -*-
from FormUI.lib import Form, Screen, Theme


def create_dashboard():
    # 一般在业务系统初始化时配置一次。
    Theme.register('demo:dashboard', {
        'button': 'fluent:dark_outlined_button',
        'label': {'fontSize': 1.2},
    }, base='fluent-dark', replace=True)
    Screen.setDefaultTheme('demo:dashboard')
    Screen.setGrid(columns=12, rows=12, gap=4, padding=8)

    form = Form.create(
        '管理面板',
        grid={'row': 1, 'column': 1, 'rowSpan': 10, 'columnSpan': 10},
        layout={'columns': [1, 2], 'rows': [1, 4, 1], 'gap': 6, 'padding': 8},
    )
    form.label('选择一个项目', grid={'row': 0, 'column': 0, 'columnSpan': 2})
    form.listview('项目', [
        {'label': '项目 A', 'value': 'a'},
        {'label': '项目 B', 'value': 'b'},
    ], grid={'row': 1, 'column': 0, 'columnSpan': 2})
    form.button('刷新', lambda playerId: refresh(playerId),
                grid={'row': 2, 'column': 0})
    form.button('关闭', lambda playerId: form.close(playerId),
                grid={'row': 2, 'column': 1})
    return form


def refresh(playerId):
    print('刷新玩家界面：%s' % playerId)
```

这里有两个坐标系：`Form.create(grid=...)` 相对屏幕网格定位整个窗口；控件的 `grid=...` 相对窗口内容区的网格定位，不包含窗口标题栏。`layout` 定义窗口内容网格，因此窗口可以占屏幕的 10×10 格，同时内部只有 2 列、3 行。

## 主题接口

| 接口 | 含义 |
| --- | --- |
| `Theme.register(name, styles, base='oreui', replace=False)` | 注册主题；继承已有主题快照，再按控件类型合并样式属性。返回 None。 |
| `Theme.get(name)` | 获取解析完成的样式副本，修改它不会修改注册表。 |
| `Theme.names()` | 返回内置及自定义主题名称。 |
| `Theme.unregister(name)` | 删除自定义主题；已创建的表单保留主题快照。 |
| `Screen.setDefaultTheme(name=None)` | 设置新表单的默认主题；None 清除设置。 |
| `Screen.getDefaultTheme()` | 查询默认主题名称，没有设置时返回 None。 |
| `Form.create(..., theme='demo:dashboard')` | 为单个表单指定主题，优先于 Screen 默认主题。 |

`styles` 支持 `scrolling_panel`、`button`、`label`、`divider`、`toggle`、`slider`、`textfield`、`dropdown`、`listview`。每项可以是 class 字符串，也可以是完整样式字典；例如 `{'button': {'class': 'project:button', 'height': 36}}`。合并按样式属性进行；嵌套属性整体替换。

`base` 可选内置或已注册的自定义主题。传 `base=None` 创建部分主题，未配置的属性继续使用控件自身默认值和 Screen 默认样式。内置主题仍为 `oreui`、`flutter`、`flutter-dark`、`fluent`、`fluent-dark`。内置名称不允许覆盖或删除，自定义名称重复注册需明确传 `replace=True`。删除当前默认主题前，先 `Screen.setDefaultTheme()` 清除默认设置。

最终优先级：控件自身默认值（启用网格时默认填满单元格）→ `Screen.setDefaultStyle` → 主题的完整样式 → 调用时 `style` → 显式 `grid` 参数。内置主题仍只提供 class，所以原有全局高度等配置继续生效。Group/Custom 的模板和 Group 注册定义不自动套用主题。

主题是静态配置，不接受 Observable、函数或其他运行时对象；需要绑定的尺寸、文字等放在具体表单或控件的 style 中。主题注册表按运行端的 Screen 管理器隔离：服务端创建表单就在服务端注册主题，客户端创建则在客户端注册。已经解析的样式随表单数据传给客户端，客户端不需要再次注册服务端的主题名称。

主题不会自动生成或注册 JSON UI 控件。若需要全新的颜色、背景、边框或字体纹理，应先编写原生 UI 模板，通过 `Control.register` 注册对应 class，再由主题引用这些 class；资源必须放入资源包并合并 `_ui_defs.json`。仅在 style 中添加 `color` 等字段，不会自动给所有原生模板染色；应由模板或其 onCreate 回调使用这些字段。

## 全局网格与表单网格

```python
Screen.setGrid(columns=12, rows=12, gap=6, padding=8)
config = Screen.getGrid()  # 独立副本；行列已展开为权重列表
Screen.clearGrid()        # 清除后续表单的默认网格

form = Form.create('局部网格', layout={
    'columns': [1, 2, 1], 'rows': 4, 'gap': 4, 'padding': 6,
})
```

| 参数 | 规则 |
| --- | --- |
| `columns` / `rows` | 正整数表示等分数量；非空列表或元组表示正权重，比例决定尺寸。默认 1，单轴最多 256 格。 |
| `gap` | 行间距和列间距，非负有限像素值，默认 0。 |
| `padding` | 四边内边距，非负有限像素值，默认 0。 |

网格先减去 padding 和 gap，再按权重分配空间；跨格尺寸包含中间间距。过小的窗口会缩小间距、将单元格尺寸压到零，避免负尺寸。

`Screen.setGrid` 同时提供**窗口定位网格**和**默认内容网格**。表单没有设置 `layout` 时继承全局内容网格；显式 `layout={...}` 覆盖内容网格，不影响窗口在屏幕中的位置。仅指定 `layout` 时无需设置 Screen 网格；指定表单 `grid` 时必须先设置 Screen 网格。

这些配置只影响当前运行端之后创建的表单，不广播修改另一端的全局配置。服务端表单会携带完整网格快照，所有收到该表单的客户端按各自屏幕尺寸计算位置。修改或清除全局设置不会改变已创建表单，包括尚未显示的表单。若要换布局配置，创建新表单。

## 指定位置和跨格

所有添加控件方法都在原有参数之后新增 `grid=None`，保持旧的位置参数兼容：

```python
form.button('确定', on_confirm, grid={'row': 0, 'column': 1})
form.label('跨两列', grid={'row': 1, 'column': 0, 'columnSpan': 2})
form.custom(params={'id': 'preview'}, style={'class': 'project:preview'},
            grid={'row': 2, 'column': 0, 'rowSpan': 2, 'columnSpan': 2})
```

`row`、`column` 必填且从 **0** 开始；`rowSpan`、`columnSpan` 默认 1，必须是正整数。位置和网格配置都是静态数据，不支持 Observable。绑定 width、height、offsetX、offsetY、visible 的原有能力保留。

也可写入 `style={'grid': {...}}`；同时提供时，方法的 `grid` 参数优先。表单同样支持 `style['grid']` 与 `style['layout']`。

布局规则：

- 先保留所有显式指定的位置，剩余控件按添加顺序逐行填入空格。
- 隐藏控件保留格子，不使其他控件换位。
- 同一内容网格内，越界、重叠和无空格都会抛错；不同表单窗口允许占用相同的屏幕格子，显示层级仍由 layer 决定。
- 网格内控件默认填满格子。显式 width、height、offsetX、offsetY 可控制格内尺寸和偏移；百分比相对跨格后的区域，`%x/%y` 同样以该区域对应轴为基准，`default` 使用模板原始尺寸。网格布局将原生锚点统一设为左上角。
- 超出格子的显式像素尺寸或偏移不会被格子裁剪，可能覆盖相邻控件；表单滚动内容会覆盖可见控件的实际底边。长列表优先使用 ListView 自带的内部滚动。
- 窗口或屏幕尺寸改变时重新计算网格。网格表单的尺寸绑定更新直接应用；旧的非网格表单继续使用原有尺寸过渡。
- 显示期间追加控件也支持 grid；新显式位置可能让已有自动排布控件换到其他空格，但不会重建已有控件。

## Group 的局部网格

Group 根可以指定自己的 `layout`，注册子控件时通过 `grid` 指定位置。嵌套 Group 的 `layout` 相对该 Group 自身尺寸。

```python
from FormUI.lib import Control, Group, Form

Control.register('demo:actions', 'fui.group', Group({
    'cancel': {
        'class': 'fluent:dark_button',
        'size': ['100%', '100%'],
        'grid': {'row': 0, 'column': 0},
    },
    'confirm': {
        'class': 'fluent:dark_primary_button',
        'size': ['100%', '100%'],
        'grid': {'row': 0, 'column': 1},
    },
}))

form = Form.create('操作', theme='fluent-dark', layout=False)
form.group({
    'cancel': {'label': '取消', 'callbacks': lambda player: form.close(player)},
    'confirm': {'label': '确定', 'callbacks': lambda player: form.close(player)},
}, style={
    'class': 'demo:actions', 'height': 36,
    'layout': {'columns': 2, 'rows': 1, 'gap': 8},
})
```

Group 子控件仍在注册阶段声明布局，实例 children 提供数据、回调和 params。子控件没有显式位置时按**子控件名称排序**自动排布，避免 Python 2 字典无序导致两端布局不同。子控件尺寸仍以注册定义为准，需要填满格子时设 `size=['100%', '100%']`。

## 原有布局兼容

没有设置全局网格且没有指定 layout 时，`Form.create(..., {'grids': [1, 2]})` 继续按列权重自动顺排并根据控件高度增长内容区。旧布局隐藏控件仍会收起空间。

已经设置 Screen 网格，但希望窗口内部使用旧布局：

```python
Screen.setGrid(columns=2, rows=1, gap=8)
form = Form.create('右侧窗口', {'grids': [1]},
                   grid={'row': 0, 'column': 1}, layout=False)
form.label('窗口使用屏幕网格，内容仍按原有顺序排列')
form.button('关闭', lambda player: form.close(player))
```

显式传入旧的 `style['grids']`，且没有显式 layout 时，也会选择旧内容布局。新 layout 与 grids 同时提供时以 layout 为准。普通窗口未指定 grid 时继续使用原有位置、尺寸和模板锚点。

## 演示与验证

`behavior/scripts/example_grid.py` 可在两端复用。接入项目示例系统后，在聊天发送：

- `fui grid`：客户端主题与网格预览。
- `fui grid-server`：服务端为当前玩家创建独立表单。
- `fui close`：关闭演示。

演示覆盖窗口定位、局部加权行列、跨列 ListView、选择状态绑定和按钮回调，并在创建后恢复先前的全局网格。

离线测试覆盖主题继承/覆盖/快照、配置校验、真实布局调用的几何结果、嵌套 Group、Observable 尺寸与偏移、屏幕尺寸变化和在线追加。仍需在网易客户端验证不同分辨率下的视觉比例、原生锚点、鼠标/触摸、ListView 内滚动，以及双端消息时序。
