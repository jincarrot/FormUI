---
name: netease-formui
description: 使用本项目 FormUI 库为网易版我的世界 ModSDK 编写客户端或服务端表单、Observable 数据绑定、OreUI/Flutter/Fluent 风格界面，以及 Group 组合控件和 Custom 原生 UI 动画。适用于接入此库、生成调用示例和排查调用问题；不负责改造 FormUI 库内部实现。
---

# FormUI 表单开发

依据项目当前公开接口编写调用代码。用户未要求落盘时，直接提供示例；要求实现时，接入宿主项目现有系统和生命周期。对无法从代码、文档或用户要求确认的业务行为、初始化约定或资源定义，先向用户提问，并继续不依赖答案的工作。

## 定位资料

本 skill 随 FormUI 项目保存。正常情况下，项目根目录为本文件所在目录的 `../../..`。优先核对宿主项目实际使用的 FormUI 版本和导入前缀；移动 skill 后，通过 `FormUI/lib.py`、`resource/ui/fui.json` 和现有调用定位库，找不到就询问库的位置。以下路径均相对 FormUI 项目根目录，不包含个人机器路径。

- 普通表单、跨端绑定和风格选择：读取 [表单用法](references/forms.md)。
- 注册模板、组合控件、原生操作或动画：读取 [Group 与 Custom](references/composition.md)。
- 布局参数细节：`docs/layout-parameters.md`。
- 完整公开签名：`behavior/scripts/FormUI/lib.pyi`、`core/general/form.pyi`、`core/general/interfaces/{form,controls}.pyi`、`interfaces/base/controls.pyi`（后三项相对库目录）。
- 风格标识：`behavior/scripts/FormUI/innerStyles.py` 的导出及 `core/general/controls/innerStyles.py`；完整风格说明在 `docs/flutter-ui.md`、`docs/fluent-ui.md`。
- 集成和游戏验证范例：`docs/test-examples.md`、`behavior/scripts/example_{c,s,shared,styles}.py`。按需读取相关部分，不照搬示例系统到业务项目。

## 实施顺序

1. 确定代码运行端、目标玩家、状态是否跨玩家共享、需要的风格。服务端表单默认按业务目标传入 `playerId`；群发展示须符合用户意图。
2. 检查宿主的脚本导入、FormUI 系统注册和资源包是否已接入。示例采用 `from FormUI.lib import ...`；宿主若使用 `scripts.FormUI` 等前缀，沿用其实际路径。
3. 在 FormUI 系统可用后创建 Form/Observable。客户端显示和依赖内置模板的注册还需等库处理完 `UiInitFinished`；参考 `example_c.py` 的延迟执行方式，避免在模块顶层创建这些对象。仅导入风格常量可使用无引擎调用的 `FormUI.innerStyles`。
4. 优先用内置控件和 Observable；需要组合布局时用 Group，需要原生 UI 操作时用客户端 Custom 回调。通过公开接口完成业务，发现库内部缺陷时说明证据，不把调用任务扩展成库改造。
5. 更新目标项目自己的业务文件及必要资源。接入资源包时合并 `ui/_ui_defs.json`，保留宿主已有条目；携带模板引用的纹理及其元数据，不直接覆盖整份资源定义。不需要演示功能时无需接入 `example_*.py`、`samples.json` 或 `fui_examples.json`。
6. 核对参数、回调、布局和生命周期，选择适合变更的验证；交付时说明运行端、调用时机、目标玩家和必要资源。

## 必须保留的接口语义

- `Form.create(title, style)` 接收显示与布局配置；`show(target=None)` 没有 `options` 参数。表单根必须使用已注册的滚动面板 class。
- 控件添加方法返回 Form，可链式调用；`show()` 返回显示结果，`result.onClose(callback)` 和 `close()` 返回 `None`。
- 按钮回调接收 `playerId` 字符串；关闭回调接收带 `playerId`、`closeReason` 的对象；Custom 回调接收原生控件与参数快照。三者不能混用。
- 正在显示或等待创建的同一玩家再次 `show()` 会抛出 `RuntimeError`。服务端关闭依赖客户端回执，需要回执后再重开。`isShowing()` 的服务端语义为历史显示过的全部玩家，不是“任一玩家”。
- Observable 使用 `create/getValue/setValue/subscribe/unsubscribe`，不编造 `.value` 属性。绑定数据用 `setValue` 更新，不通过 Form 的内部成员查找原生控件。
- 下拉框 `items`、选项 `label/value` 为静态数据；菜单标题和选中值可绑定 Observable。面板风格不会自动替换子控件 class。
- 游戏侧代码保持 Python 2.7 兼容，使用 UTF-8 声明，避免 f-string、运行时类型注解和 Python 3 专有语法；不使用 `numbers` 库。项目 `.pyi` 和开发工具的 Python 3 写法不能直接复制到游戏脚本。

## 验证与故障判断

检查公开签名、注册标识、原生子路径、资源定义和实际运行端。若 `getSystem()` 为 `None`，确认调用时机、导入前缀及系统配置，向用户索取必要的完整堆栈；不靠创建假的系统对象或替换跨端检测来掩盖问题。

宿主已有测试时，验证本次业务逻辑。若要验证当前库的已有能力，可在项目根目录用 Python 3 运行 `python -B -m unittest discover -s tests`；这套离线测试使用 SDK 替身，不能证明游戏中的渲染、触摸和跨端时序正常。

按功能选择游戏内验证：显示/关闭/重开、控件输入、Observable 更新；有 Group/Custom 时补查尺寸变化和关闭后停止更新；有多玩家共享时分别验证同步与关闭行为。`fui ...` 是此项目演示系统提供的聊天消息，其他宿主未接入该系统时不能直接使用。新增原生 SDK 调用应核对对应网易 SDK 文档，不猜测方法和参数。
