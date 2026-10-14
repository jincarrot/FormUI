# Group 控件

`Group` 用命名字典组合已注册的控件。第二个注册参数是组的原生根模板路径；库内提供空面板 `fui.group`，也可以使用自己的 panel 模板。每个子控件直接创建在这个根节点下。

```python
from FormUI.lib import Control, Group, Form, Observable

child_width = Observable.create("100%")
child_visible = Observable.create(True)

# 内置 oreui 控件完成注册后执行。
Control.register("demo:group", "fui.group", Group({
    "title": {
        "class": "oreui:label",
        "offset": [0, 0],
        "size": [child_width, 24],
        "visible": child_visible,
    },
    "confirm": {
        "class": "oreui:normal_btn_thin",
        "offset": [0, 28],
        "size": ["100%", 32],
    },
}))

text = Observable.create("初始标题")
group_width = Observable.create(200)


def on_confirm(playerId):
    text.setValue("已确认")


form = Form.create("Group 示例", {"class": "oreui:light_panel_thin"})
form.group(
    {
        "title": {"label": text},
        "confirm": {"label": "确认", "callbacks": {"onClick": on_confirm}},
    },
    {"class": "demo:group", "width": group_width, "height": 60},
)
form.show()

group_width.setValue(300)       # 两个子控件随父组变宽。
child_width.setValue("50%")    # 标题宽度变为组宽度的一半。
child_visible.setValue(False)  # 隐藏标题，不移动组内其他子控件。
```

## 注册配置

每个子控件只接受 `class`、`offset`、`size`、`offsetX`、`offsetY`、`width`、`height`、`visible`。`class` 必填，引用已注册的控件标识；子控件名称必须非空且不包含 `/`。

`offset` 和 `size` 接受恰好包含两个元素的列表，也接受值为这种列表的 Observable。列表元素可以分别绑定 Observable。`offsetX`、`offsetY`、`width`、`height` 存在时覆盖对应列表元素，更新列表 Observable 后仍保持这个优先级。

尺寸和位移接受数字或已有的尺寸表达式，例如 `100%`、`50%-8px`、`default`。未指定尺寸时保留子模板默认尺寸，未指定偏移时使用零，可见性默认 `True`。`visible` 接受布尔值或布尔 Observable。子控件的 `class` 也可绑定 Observable，切换时重建该子控件并清理旧实例的输入轮询与回调记录。

组内使用绝对定位；百分比宽高与位移相对于直接父组计算，父表单的 grids 只排列组的根节点。组的默认高度为根模板高度，需要较大空间时显式指定 height；子控件不会自动撑高组。

## 实例数据

`form.group(children={}, style={}, params={})` 返回表单，支持链式调用。`style` 定义组自身的尺寸、位移和可见性，也支持 offset/size 简写以及 Observable。`params` 传给组根的 `onCreate(args)`，通过 `args.params` 读取。

`children` 按注册的子控件名称提供数据，字段沿用对应控件：`label`、`state`、`value`、`minValue`、`maxValue`、`step`、`items`、`callbacks`；各类型都可以用 `params` 提供创建参数。子控件参数与组根参数相互独立，不自动继承；Custom 的参数仍用于原有更新通知。省略子控件数据时使用该类型的空文本、初始值和空回调等默认值。子控件样式统一由 Group 注册配置定义。

回调在调用 form.group 的一端保存，传输使用回调编号。输入控件将 Observable 更新发往该 Observable 所属端，组内绑定的客户端 Observable 与服务端 Observable 都可以使用。

注册在客户端完成即可由服务端显示实例。服务端也可以注册不含 onCreate 回调的 Group，定义会同步给客户端；普通注册配置支持 Observable。

## 嵌套与生命周期

子控件可以引用另一个 Group，其实例数据通过 `children` 继续传入：

```python
form.group(
    {"inner": {"children": {"title": {"label": text}}}},
    {"class": "demo:outer", "height": 100},
)
```

创建时先完成整体布局，再从内部子控件到父组执行 onCreate。内部 custom 沿用原有的参数快照和 oldValue/newValue 通知；创建前收到的更新按顺序排队。组实例之间的同名子控件独立定位。表单关闭时清理整个组的原生引用、输入轮询和待处理通知。

循环组引用、未注册的子控件 class、未知的实例子控件名称及非法列表长度会报错。
