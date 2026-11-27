# MoreUI 兼容接口

`FormUI.moreui` 用于迁移使用旧版 MoreUI 的项目。它复用 FormUI 的客户端和服务端系统。六个公开类的说明以 `【已废弃】` 开头，Python 类名保留原样，旧调用仍可以按原名导入。新项目可直接使用 `FormUI.lib`。

## 导入

在原来导入 `MoreUI.lib` 的服务端脚本中，把导入路径改为 `FormUI.moreui.lib` 或 `FormUI.moreui`，并在客户端初始化脚本中 `import FormUI.moreui.register`。如果客户端已导入 `FormUI.lib`，现有导入已完成注册。资源包需要包含 FormUI 的 `ui/` 资源，其中 `ui/_ui_defs.json` 引用 `ui/moreui.json`。

```python
# 服务端脚本
from FormUI.moreui import BarForm, ConfigMenu, CustomForm, MoreUI, Observable, SidebarForm

# 客户端初始化脚本
import FormUI.moreui.register
```

## 创建单独的表单

客户端 UI 就绪后，在服务端用 `playerId` 创建表单。控件方法可以链式调用，`button` 回调沿用旧版的无参数写法。文本框、开关、滑块和下拉框绑定 `clientWritable=True` 的兼容层 `Observable`。

```python
# -*- coding: utf-8 -*-
from FormUI.moreui import CustomForm, Observable

def openSettings(playerId):
    name = Observable.create('玩家', {'clientWritable': True})
    expanded = Observable.create(False, {'clientWritable': True})
    level = Observable.create(1, {'clientWritable': True})
    items = [{'label': '低', 'value': 1}, {'label': '高', 'value': 3}]

    form = CustomForm.create(playerId, name, {'movable': True})
    form.textField('修改标题', name)
    form.toggle('显示详细设置', expanded)
    form.divider({'visible': expanded})
    form.slider('强度', level, 1, 3, {'visible': expanded})
    form.dropdown('档位', level, items, {'visible': expanded})
    form.button('关闭', lambda: form.close())
    return form.show()
```

用 `observable.getData()` 读取、`observable.setData(value)` 修改数据，或用 `observable.subscribe(callback)` 接收新值。`show()` 和 `close()` 继续操作创建时绑定的玩家。

## 在一个界面放多张表单

`MoreUI.create(playerId, layout)` 的 `column` 和 `row` 是列宽与行高的相对权重。每张子表单使用从零开始的 `position=[列, 行]`，`size=[跨列数, 跨行数]`，以及可选的 `offset=[横向, 纵向]`、`margin=[上, 右, 下, 左]` 和 `layer`。偏移与边距使用 UI 像素。

```python
def openDashboard(playerId):
    ui = MoreUI.create(playerId, {'column': [1, 3], 'row': [1]})
    bar = ui.addBarForm('菜单', {'closable': True}, {'position': [0, 0]})
    page = ui.addCustomForm('详情', layout={'position': [1, 0], 'margin': [4, 4, 4, 4]})

    bar.mayCloseAll = True
    bar.form.button('收起详情', lambda: page.form.close())
    bar.form.button('展开详情', lambda: page.form.show())
    page.form.label('详情内容')
    ui.show()
    return ui
```

用 `ui.addForm(form, layout)` 加入已有的 `CustomForm` 或 `BarForm`。返回值的 `.form` 和 `.layout` 可供后续操作。`ui.removeForm(返回值)` 会移除该表单，`ui.close()` 会关闭整个组合。对单张表单调用 `close()` 只收起该表单。将 `mayCloseAll` 设为 `True` 后，玩家点该表单的关闭按钮会关闭整个组合。

| 入口 | 常用方法 |
| --- | --- |
| `CustomForm` | `button`、`label`、`divider`、`spacer`、`textField`、`toggle`、`slider`、`dropdown`、`custom` |
| `BarForm` | `button`。`direction` 支持 `vertical` 和 `horizontal` |
| `SidebarForm` | `tab('textures/ui/gear', form)` 添加图标页，打开时显示第一项 |
| `ConfigMenu` | `addPage(form, tabName)` 添加设置页，可省略名称以使用表单标题。打开时等待玩家选择页面 |

`movable`、`resizable`、`closable` 分别控制拖动窗口、调整大小和关闭按钮，也可以绑定兼容层的布尔 `Observable`。`style` 可以使用 FormUI 的主题名。兼容层沿用 FormUI 的控件和主题绘制界面，未知样式名使用 OreUI。`CustomForm.custom(identifier, params)` 使用通过 FormUI 注册的控件标识符。
