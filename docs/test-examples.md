# 攻击实体时打开表单

加载项目的行为包和资源包，进入世界后，空手或持近战武器攻击一只生物。表单通过 `layout={'combineUI': True}` 挂在攻击者 HUD 的左侧，第一行显示受击实体的 ID。表单使用 `root='fui:panel'` 的透明固定底板，控件使用 Fluent 深色风格。

| 操作 | 可见结果 |
| --- | --- |
| 将「强度」从 5 拖到 8 | 数字变为 `8/10`，强度条显示 `[########--]` |
| 点击「强度 +1」 | 滑块和强度条一起前进一步，从 10 再点一次会回到 0 |
| 关闭「显示强度条」，调整强度，然后重新打开 | 强度条先隐藏，再以最新的数值显示 |
| 在「备注」输入文字，再清空 | 下方标签回显输入内容，清空后显示「（空备注）」 |
| 关闭表单，再攻击另一个实体 | 表单从 HUD 移除，再次显示时目标 ID 更新，强度、开关和备注保留本次游戏中的值 |

每个客户端复用自己的表单。窗口正在创建或已经打开时，再次收到攻击事件只更新目标。滑块和按钮写入同一个 Observable，强度条通过 `map` 生成，开关绑定在强度条的 `visible` 属性上。[表单源码](../behavior/scripts/attack_form.py) · [客户端事件入口](../behavior/scripts/attack_client.py) · [SDK 攻击事件](https://github.com/MCNeteaseDevs/mc-netease-sdk/blob/main/1-ModAPI/%E4%BA%8B%E4%BB%B6/%E7%8E%A9%E5%AE%B6.md#playerattackentityevent)

表单使用资源包内的预生成控件。修改固定控件结构后，可在项目根目录重新生成资源。[JSON UI 模板](../resource/ui/formui_generated/fui_generated_examples/attack.json)

```console
python tools/compile_form.py behavior/scripts/attack_form.py create_attack_form fui_generated_examples.attack --resource-pack resource
```
