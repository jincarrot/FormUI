---
name: netease-formui
description: 使用本项目 FormUI 库为网易版我的世界 ModSDK 编写客户端或服务端表单、Observable 数据绑定、OreUI/Flutter/Fluent 风格界面，以及 Group 组合控件和 Custom 原生 UI 动画。适用于接入此库、生成调用示例和排查调用问题；不负责改造 FormUI 库内部实现。
---

# FormUI 表单开发

依据项目当前公开接口编写调用代码。用户未要求落盘时，直接提供示例；要求实现时，接入宿主项目现有系统和生命周期。对无法从代码、文档或用户要求确认的业务行为、初始化约定或资源定义，先向用户提问，并继续不依赖答案的工作。

## 定位资料

本 skill 随 FormUI 项目保存。正常情况下，项目根目录为本文件所在目录的 `../../..`。优先核对宿主项目实际使用的 FormUI 版本和导入前缀；移动 skill 后，通过 `FormUI/lib.py`、`resource/ui/fui.json` 和现有调用定位库，找不到就询问库的位置。以下路径均相对 FormUI 项目根目录，不包含个人机器路径。

- 普通表单、跨端绑定和风格选择：读取 [表单用法](references/forms.md)。
- 新版简洁调用、表单主题及 Observable 辅助方法：`docs/api-design.md`；动态列表与三种风格：`docs/listview.md`。
- 自定义主题注册、全局 Screen 网格、表单/控件定位和 Group 局部网格：`docs/themes-grid.md`。
- 注册模板、组合控件、原生操作或动画：读取 [Group 与 Custom](references/composition.md)。
- 复杂表单的开发时导出和模板绑定见 `docs/compiled-forms.md`。使用 `tools/compile_form.py` 生成资源，再通过 `form.bindTemplate('my_forms.settings')` 绑定当前固定控件。
- 布局参数细节：`docs/layout-parameters.md`。
- 完整公开签名：`behavior/scripts/FormUI/lib.pyi`、`core/general/form.pyi`、`core/general/interfaces/{form,controls}.pyi`、`interfaces/base/controls.pyi`（后三项相对库目录）。
- 风格标识：`behavior/scripts/FormUI/innerStyles.py` 的导出及 `core/general/controls/innerStyles.py`；完整风格说明在 `docs/flutter-ui.md`、`docs/fluent-ui.md`。
- 游戏内接入参考 `behavior/scripts/attack_client.py` 与 `behavior/scripts/attack_form.py`。操作与预期结果见 `docs/test-examples.md`。

## 实施顺序

1. 确定代码运行端、目标玩家、状态是否跨玩家共享、需要的风格。服务端表单默认按业务目标传入 `playerId`；群发展示须符合用户意图。
2. 检查宿主的脚本导入、FormUI 系统注册和资源包是否已接入。当前版本在两端各自导入 `FormUI.lib` 时自动注册对应端系统；只导入包或 innerStyles 不会注册。示例采用 `from FormUI.lib import ...`；宿主若使用 `scripts.FormUI` 等前缀，沿用其实际路径。
3. 在 FormUI 系统可用后创建 Form/Observable。客户端显示和依赖内置模板的注册还需等库处理完 `UiInitFinished`；可参考 `attack_client.py` 在 UI 就绪后监听本地玩家攻击实体的方式。仅导入风格常量可使用无引擎调用的 `FormUI.innerStyles`。
4. 优先用内置控件和 Observable；需要组合布局时用 Group，需要原生 UI 操作时用客户端 Custom 回调。通过公开接口完成业务，发现库内部缺陷时说明证据，不把调用任务扩展成库改造。
5. 更新目标项目自己的业务文件及必要资源。接入资源包时合并 `ui/_ui_defs.json`，保留宿主已有条目；携带模板引用的纹理及其元数据，不直接覆盖整份资源定义。`attack_client.py`、`attack_form.py` 与对应的预生成模板仅供本项目游戏内示例使用。
6. 核对参数、回调、布局和生命周期，选择适合变更的验证；交付时说明运行端、调用时机、目标玩家和必要资源。

## 必须保留的接口语义

- `Form.create(title="", style=None, theme=None, grid=None, layout=None, root=None)` 支持内置或 Theme.register 注册的主题。省略 theme 使用 Screen 默认主题。`root='fui:panel'` 使用透明固定面板，也可传入已注册的 `Panel` 或 `ScrollingPanel` 标识。显式 root 优先于 `style['class']`。`Panel(contentPath='/body')` 可指定内容子面板，标题和关闭按钮路径可选。创建时传 `layout={'combineUI': True}` 会让该表单每次显示时嵌入玩家当前的 ScreenNode，默认 `False` 使用独立页面。`show(target=None, onClose=None)` 指定玩家和关闭回调，`close()` 仅移除嵌入的表单。
- `Theme.register(name, styles, base='oreui', replace=False)` 按控件类型合并静态样式；在创建表单的一端注册，解析后的样式随表单发送。主题不自动生成/注册 JSON UI，也不自动将任意 color 字段应用到原生控件。
- `Screen.setGrid(columns, rows, gap=0, padding=0)` 给新表单提供屏幕定位及默认内容网格；Form 的 grid 相对屏幕、控件的 grid 相对内容区，row/column 从 0 开始，支持 rowSpan/columnSpan。layout 提供行列时覆盖内容网格，只提供 combineUI 时沿用当前内容布局，layout=False 使用顺排；配置和位置不绑定 Observable。隐藏控件保留格子，显式位置先占位，其他控件填空。完整参数与 Group 行为查 `docs/themes-grid.md`。
- 控件添加方法返回 Form，可链式调用；`show()` 返回显示结果，`result.onClose(callback)` 和 `close()` 返回 `None`。
- 按钮第二参数可直接传点击函数，或 onClick/onMoveIn/onMoveOut 字典，回调接收 `playerId`；关闭回调接收带 `playerId`、`closeReason` 的对象；Custom 回调接收原生控件与参数快照。三者不能混用。
- 注册控件的 `onCreate` 另提供 `args.style`，为当前实例合并默认项、解包 Observable 后的独立样式快照；可读取普通控件 style 的自定义字段，不能靠修改快照更新控件，也不能把它当注册 options。
- 除 `custom(params, style)` 外，添加控件方法均在 `style` 后接收可选的 `params={}`，由创建回调的 `args.params` 读取实例快照；业务数据优先放 params。Group 根和各子控件分别传参，普通控件 params 不会触发 Custom 更新通知。
- 正在显示或等待创建的同一玩家再次 `show()` 会抛出 `RuntimeError`。服务端关闭依赖客户端回执，需要回执后再重开。`isShowing()` 保留服务端历史全部玩家语义；查询任意玩家用 `isAnyShowing()`，当前在线显示列表用 `getShowingPlayers()`。服务端空目标集合为无操作，None 才代表全部在线玩家。
- Observable 使用 `create/getValue/setValue/subscribe/unsubscribe`，不编造 `.value` 属性。`update(fn)` 基于独立副本返回新值，重入时依次计算；`map(fn)` 创建派生值；`watch(fn, immediate=True)` 返回幂等取消函数。变更回调期间 getValue 仍为旧值，业务使用回调传入的新值。
- Dropdown 的 items 及行字段保持静态；ListView 的 items 可绑定整个列表的 Observable，行内 label/value 为普通数据且 value 唯一。只指定面板 class 不会推断子控件风格，需要统一风格时使用 theme。
- 游戏侧代码保持 Python 2.7 兼容，使用 UTF-8 声明，避免 f-string、运行时类型注解和 Python 3 专有语法；不使用 `numbers` 库。项目 `.pyi` 和开发工具的 Python 3 写法不能直接复制到游戏脚本。

## 验证与故障判断

检查公开签名、注册标识、原生子路径、资源定义和实际运行端。若 `getSystem()` 为 `None`，确认调用时机、导入前缀及系统配置，向用户索取必要的完整堆栈；不靠创建假的系统对象或替换跨端检测来掩盖问题。

宿主已有测试时，验证本次业务逻辑。若要验证当前库的已有能力，可在项目根目录用 Python 3 运行 `python -B -m unittest discover -s tests`；这套离线测试使用 SDK 替身，不能证明游戏中的渲染、触摸和跨端时序正常。

按功能选择游戏内验证：显示/关闭/重开、控件输入、Observable 更新；有 Group/Custom 时补查尺寸变化和关闭后停止更新；有多玩家共享时分别验证同步与关闭行为。本项目的游戏内用例由本地玩家攻击实体触发。新增原生 SDK 调用应核对对应网易 SDK 文档，不猜测方法和参数。
