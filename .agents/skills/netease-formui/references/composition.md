# Group、Custom 与原生操作

需要本参考时，同时核对项目 `docs/group-controls.md`、`docs/custom-controls.md` 的相应部分。注册标识（如 `demo:summary`）与原生模板路径（如 `fui.group`）是两种参数；style.class 使用注册标识。

## 注册与资源

`Control.register(identifier, controlPath, descriptor)` 的 descriptor 是 `Button/Label/Toggle/Slider/Textfield/Dropdown/Divider/ScrollingPanel/Group/Custom` 等公开描述类实例。普通模板的按钮、标签、输入子路径通过相应描述类参数指定，以实际 JSON 为准。

客户端注册保存到该客户端；不会自动为服务端注册同一个描述对象。服务端仍可在表单中引用已在目标客户端注册的 class。服务端无原生回调的注册会广播给客户端，且在客户端 UI 初始化请求时补发。避免两端用同一标识注册不同定义。

带 `onCreate` 或 `onObservableUpdate` 的描述只能在客户端注册；服务端可以注册没有这些回调的模板和 Group。Group 中普通按钮的业务回调由 `form.group` 调用端保存，不受这条原生回调限制。

新的原生模板先写入宿主资源包的 UI JSON，将文件合并进 `ui/_ui_defs.json`，再用 namespace.control_name 注册。模板所用贴图一同携带。组合已注册类型时使用 Group，无需为每个组合另写一份固定子控件 JSON。

## Group 示例

下面注册在客户端内置风格完成注册后执行；实例数据可由客户端或服务端提供。

```python
# -*- coding: utf-8 -*-
from FormUI.lib import Control, Group, Form, Observable
from FormUI.innerStyles import InnerStyles


def register_summary():
    Control.register('demo:summary', 'fui.group', Group({
        'title': {
            'class': InnerStyles.fluent.Label,
            'offset': [0, 0], 'size': ['100%', 24],
        },
        'confirm': {
            'class': InnerStyles.fluent.PrimaryBtn,
            'offset': [0, 28], 'size': ['100%', 38],
        },
    }))


def create_summary():
    text = Observable.create('等待确认')
    width = Observable.create(200)

    def confirm(playerId):
        text.setValue('已确认')

    form = Form.create('组合示例', {'class': InnerStyles.fluent.LightPanel})
    form.group({
        'title': {'label': text},
        'confirm': {'label': '确认', 'callbacks': {'onClick': confirm}},
    }, {'class': 'demo:summary', 'width': width, 'height': 70})
    return form, width
```

注册配置每个命名子控件的 class 必填；只接受 class、offset、size、offsetX、offsetY、width、height、visible。名称非空且不含 `/`。offset/size 为两个元素的列表，可整体或按元素绑定 Observable；独立轴键覆盖简写，class/visible 也支持 Observable。class 变化会重建子控件。

`form.group(children, style, params={})` 的 params 传给组根的创建回调。实例 children 按注册名称传入数据：label、state、value、minValue、maxValue、step、items、callbacks；所有类型可单独提供 params，嵌套 Group 使用 children。各层 params 不自动继承或合并；普通控件只在 onCreate 读取参数，Custom 保留更新通知。不要把文本或回调放进注册布局字典，也不要在实例数据中编造子控件 style。

子控件绝对定位，百分比相对直接父组；父组改变大小会更新子控件。组不会按内容自动撑高，应显式预留 height。注册配置中的 Observable 被多个实例共用时会共同改变布局；需要实例独立大小时优先绑定 form.group 的根 style。嵌套组引用须无环，实例数据的名称须存在于定义中。

## Custom 示例

下面复用库中的 `fui_ore_base.label`，其标签子路径为 `/label`。客户端注册一次，之后两端均可用 `demo:native_label` 创建实例。

```python
# -*- coding: utf-8 -*-
from FormUI.lib import Control, Custom, Form, Observable
from FormUI.innerStyles import InnerStyles


def on_create(args):
    args.control.GetChildByPath('/label').asLabel().SetText(
        str(args.params.get('text', '')))


def on_update(args):
    if args.key == 'text':
        args.control.GetChildByPath('/label').asLabel().SetText(str(args.newValue))


def register_native_label():
    Control.register('demo:native_label', 'fui_ore_base.label', Custom(
        onCreate=on_create, onObservableUpdate=on_update))


def create_custom_form():
    text = Observable.create('初始文字')
    form = Form.create('原生示例', {'class': InnerStyles.oreui.LightPanel})
    form.custom({'text': text}, {'class': 'demo:native_label', 'height': 24})
    return form, text
```

`onCreate(args)` 在本实例布局完成后调用，提供 args.control、args.screenNode、args.params 和 args.style。args.style 是当前实例合并默认项后的独立样式快照，递归解包 Observable，并保留普通控件 style 中的 name 等自定义字段；Group 的布局简写会规范化。它适用于 Button、Custom 和 Group 等创建回调，不是注册 options，也不会随后续更新变化。不要通过修改快照控制原生控件。更新回调另有 key、oldValue、newValue；params 为当前解包快照。不要根据绑定编号查询另一端 Observable，不把快照当源对象修改。

params 支持普通值、值为列表/字典的 Observable 及嵌套绑定。更新按顶层键通知：`{'config': {'angle': angle}}` 的 key 为 config，oldValue/newValue 为整个 config 字典。创建前通知会排队，初始化使用最新快照，之后通知仍按各次变化提供旧值与新值。普通参数只初始化；运行时更新使用 Observable。

不同实例共用同一注册回调时，操作 args.control 对应的当前实例。需要保存原生引用时按实例记录，关闭后清理，重开后重新绑定。Group 内 Custom 同样遵循这些规则，生命周期回调从内层到外层执行。

## 动画与生命周期

图片旋转、缩放等操作在客户端 Custom 中通过 args.control 的实际图片子控件调用原生接口。按钮业务状态与旋转角度通过 Observable 保存；逐帧调度可使用 `args.screenNode.addRepeatFunc(callback, 1)`。

注意 times 是执行次数：当前实现每次 Screen.Update 调用一次回调，达到指定次数后移除；`times=1` 表示下一帧执行一次，并非永久循环或帧间隔。持续动画可在回调末尾安排下一次执行，暂停时停止修改角度；关闭或实例令牌失效时不再安排后续回调。不要修改库的 Update 方法或私有队列，也不要编造 removeRepeatFunc 接口。

完整生命周期示例见 `behavior/scripts/example_c.py` 的 onSquaresCreate、onSquaresUpdate、forgetMotion、showAnimation，以及 `resource/ui/fui_examples.json`。其方框动画每帧转 2 度，以 Observable 控制角度和运行状态；原生 Rotate/SetSize 的参数以当前 SDK 为准。

要在另一项目复用这个示例，需接入其原生模板和 `textures/ui/square` 资源，重新选择业务事件入口；聊天触发、实例键和两个方框的几何公式是演示逻辑，不是所有 Custom 的要求。
