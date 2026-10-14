# custom 控件

在客户端用 `Control.register` 注册模板及回调，然后通过 `form.custom(params, style)` 添加实例。表单和绑定的 Observable 可以由客户端或服务端创建；回调使用传来的值，不查询另一端的 Observable 对象。

```python
from FormUI.lib import Control, Custom, Form, Observable

def on_create(args):
    label = args.control.GetChildByPath('/label').asLabel()
    label.SetText(str(args.params.get('text', '')))

def on_update(args):
    if args.key == 'text':
        label = args.control.GetChildByPath('/label').asLabel()
        label.SetText(str(args.newValue))

Control.register(
    'example:custom_label',
    'fui_ore_base.label',
    Custom(onCreate=on_create, onObservableUpdate=on_update),
)

text = Observable.create('初始内容')
form = Form.create('custom 示例', {'class': 'oreui:light_panel_thin'})
form.custom({'text': text}, {'class': 'example:custom_label', 'height': 24})
form.show()
text.setValue('更新内容')
```

`onCreate` 在控件创建并完成布局后调用一次。`args.control` 是本实例的原生控件，`args.screenNode` 是所属页面，`args.params` 是解包后的初始参数快照，`args.style` 是本实例合并默认配置后的样式快照。样式中的 Observable 同样解包为当前值，修改快照不会改动原始样式或绑定值；详见[创建回调中的实例样式](layout-parameters.md#创建回调中的实例样式)。

`onObservableUpdate` 提供同一实例的 `control`、`screenNode`，以及 `key`、`oldValue`、`newValue`。`args.params` 是回调时的当前参数快照。多个实例共用同一个注册回调时，直接使用 `args.control` 更新目标实例。

`params` 支持普通值、值为列表或字典的 Observable，以及包含 Observable 的嵌套列表/字典。嵌套更新按顶层参数名通知，例如 `{'config': {'angle': angle}}` 中的 `angle` 变化时，`key` 为 `'config'`，旧值和新值是整个 `config` 字典。同一顶层参数内多处绑定同一个 Observable，每次更新仅通知一次。

参数快照不暴露绑定编号，修改快照不会修改原始 Observable 或表单缓存。普通参数只用于初始化；需要运行时更新的值使用 Observable。

控件创建前收到的通知会排队，在 `onCreate` 完成后按接收顺序触发。初始化读取最新快照；旧值和新值仍描述各次变化，因此回调应使用 `newValue` 处理本次通知。关闭表单后停止向其 custom 实例发送通知。

`onCreate` 和 `onObservableUpdate` 均可省略。服务端可注册无回调的模板；需要原生 UI 操作的回调在客户端注册。
