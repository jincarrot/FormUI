# 聊天触发的功能测试样例

客户端和服务端样例已由 `behavior/scripts/modMain.py` 注册。加载本项目的行为包与资源包、进入测试世界后，直接在聊天栏输入以下消息，**不加 `/`**。只有以 `fui` 为首个单词的消息会被拦截，其他聊天照常处理。

| 聊天消息 | 行为 |
| --- | --- |
| `fui client` | 打开客户端创建的完整功能展台，包含双正方形动画 |
| `fui server` | 服务端为发送消息的玩家创建独立的完整功能展台 |
| `fui animation` | 单独打开双正方形动画，便于观察 |
| `fui shared` | 将同一个服务端共享表单显示给自己；多个玩家分别输入可验证跨玩家同步 |
| `fui all` | 将共享表单显示给所有在线且尚未显示该表单的玩家 |
| `fui cancel-client` | 客户端连续调用 `show()`、`close()`，验证创建期间关闭 |
| `fui cancel-server` | 服务端连续发送显示、关闭，验证关闭回执及创建取消 |
| `fui close` | 关闭发送消息玩家的全部 FormUI 表单 |
| `fui help` | 查看指令帮助 |
| `fui flutter` | Flutter / Material 浅色控件预览 |
| `fui flutter-dark` | Flutter / Material 深色控件预览 |
| `fui fluent` | Fluent Qt 浅色窗口预览，标题栏仅保留关闭按钮 |
| `fui fluent-dark` | Fluent Qt 深色窗口预览 |
| `fui compare` | 同一屏幕并排显示 OreUI、Flutter、Fluent，内容与绑定数据相同 |

`fui client` 和 `fui server` 只打开自己的表单，状态按玩家隔离。`fui shared` / `fui all` 有意共用状态。关闭后再次输入指令，会重新显示同一个表单对象并保留其 Observable 状态；已经显示时输入指令只提示，可在表单内按“重复 show”测试原生错误。

## 文件与职责

- `behavior/scripts/example_c.py`：客户端入口、Custom 原生创建与更新回调、逐帧动画。
- `behavior/scripts/example_s.py`：服务端聊天分发、每玩家表单、共享表单、消息反馈和无原生回调的控件注册。
- `behavior/scripts/example_shared.py`：两端共用的公开接口演示，避免两份展台实现产生差异。
- `behavior/scripts/example_styles.py`：三种风格的同时对比，共享 Observable 数据。
- `resource/ui/fui_examples.json`：Custom 文本和动画原生模板，已加入 `_ui_defs.json`。
- `resource/textures/ui/square.png`：256×256、4 像素白色边框、透明内部、无外部留白。两个图片控件共用此贴图，分别由原生模板染成蓝色和橙色。
- `tools/generate_square_texture.py`：可复现贴图的几何生成脚本，仅开发时使用，无运行时依赖。

样例按网易 ModSDK 的 Python 2 运行环境编写。生成贴图脚本及离线测试使用 Python 3。

## 三种风格同时对比

输入 `fui compare`，从左到右显示 OreUI、Flutter、Fluent 三张浅色表单。每张宽度占屏幕 30%，中心横向偏移分别为 -32%、0%、32%，高度为 88%，内部内容可独立滚动。三张均不隐藏其他表单；如果此前已打开其他展台，可先输入 `fui close`。

每张表单都展示相同的标题文本、说明、名称输入框、画质菜单、音效开关、音量滑动条、分割线、实时名称、计数和按钮。名称、开关、音量、画质、计数与反馈共用同一组 Observable；任意一张上的修改会同步到另外两张。控件保留各自风格的默认大小和间距。

“点击 +1”同步增加计数，“恢复默认”同步重置数据，“关闭三张表单”关闭整组；标题栏关闭按钮只关闭所在表单。再次输入 `fui compare` 只补开已关闭的表单，并保留数据。`fui close` 同样可以关闭整组。

## 展台覆盖与检查方式

| 功能 | 操作与预期 |
| --- | --- |
| Button、Label、Divider | 三种按钮样式、两种分割线；点击与移入/移出回调显示 `playerId` |
| Textfield、Toggle | 修改输入框，关联文本自动更新；开关控制按钮可见性，隐藏后自动重新排列 |
| Dropdown、多列布局 | 两列各有 8 项菜单，分别展开/切换/选中；邻列和下方控件不应被推移，滚动范围容纳展开菜单 |
| Slider 边界 | 切换整数、连续模式、反向边界与负步长、相等边界、小数步长；标签和滑块同步，越界原始值仅在展示时钳制 |
| Observable 运算与订阅 | 点击计数影响派生宽度和 `count >= 2` 可见性；字符串拼接自动更新；订阅回调用 `getValue()` 读取旧值，参数读取新值；可取消并恢复订阅 |
| 字体、根几何 | 循环字体缩放 1/1.5/default；设置小数百分比、跨轴 `%y` 和负偏移，再恢复根几何 default |
| Group 与嵌套 | 子组包含文本、按钮，父组包含菜单、开关和 Custom；修改组的列表 Observable 尺寸/位移，内部 `100%` 随父组变化；独立轴属性覆盖 offset 列表 |
| Custom 实例与容器值 | 修改文本、替换列表和字典 Observable；原生回调显示参数、旧值/新值并更换文字颜色；两个 Custom 实例独立显示；Group 内 Custom 同样更新 |
| 注册与补发 | 服务端启动时注册 Label、嵌套 Group，不带原生回调；后来加入的玩家运行 `fui server` 应得到完整定义；客户端注册的 Custom 可由服务端表单引用 |
| 显示后 / 创建期间追加 | 展台第一次 show 后立即追加文本；客户端 Custom.onCreate 中再追加文本；按钮追加一对控件，滚到底部查看，原有输入和回调应保留 |
| 默认样式 | 临时设置 Label 的默认字体，追加文本后恢复空默认配置。`Screen.setDefaultStyle` 会跨端同步，因此请在测试世界演示 |
| 重复显示与状态查询 | 再次 show 同一玩家应得到 RuntimeError；isShowing 查询显示在聊天反馈中 |
| 弹层、layer、hideOtherForms | 打开第二张深色表单并隐藏主表单；关闭弹层后恢复主表单 |
| 关闭与重开 | API close、右上角关闭、closeAllForms 均有关闭反馈；重开在关闭回执之后安排，服务端异步 close 不会立即再次 show |
| 多玩家 | 两人分别打开独立服务端展台，计数互不影响；共享展台计数同步，各自关闭只影响自己；查询“全部”按历史显示过的玩家计算 |

下拉菜单选项使用静态 `items`，仅菜单选中值绑定 Observable。列表/字典通过 `setValue(新对象)` 替换；直接原地修改容器不会自动通知。

服务端网络显示受消息到达时机影响，`cancel-server` 可能短暂出现后关闭；`cancel-client` 更适合验证本地尚在创建时的取消。测试时不要把命令当作 `/fui` 游戏命令输入。

## 双正方形动画

运行 `fui animation` 后点击图内“开始”：蓝框每个 FormUI `Screen.Update` 帧旋转 2°，橙框保持 0°，只更新大小；再次点击暂停。角度滑动条、运行开关和图内按钮绑定同一组客户端 Observable，暂停时仍可拖动角度；归零和 45° 按钮同时暂停动画。

两框同心，蓝框边长为 `S`、角度为 `θ`，橙框边长为：

```text
L = S / (abs(cos θ) + abs(sin θ))
```

因此橙框四顶点始终位于蓝框边上。0° 时两框重合，45° 时橙框边长为 `S / sqrt(2)`；画布变大或缩小时重新计算 `S`。贴图复用并通过模板染色，蓝框和橙框的几何轮廓一致。边框有实际像素厚度，公式约束的是正方形轮廓的外边界。

原生操作通过 Custom 回调拿到 `args.control` 后执行：图片 `Rotate`、`SetSize`，文本 `SetText`、`SetTextColor`，按钮 `SetButtonTouchUpCallback`。逐帧回调由当前 Screen 的 `addRepeatFunc(..., 1)` 安排，不修改库内 Update，也不访问私有成员。关闭时删除实例令牌、暂停运行，旧回调下一次执行时退出；重新显示后为新的原生实例重新绑定。

## SDK 依据与验证限制

聊天入口及 `cancel` 字段使用 [网易 SDK 的 ServerChatEvent](https://github.com/MCNeteaseDevs/mc-netease-sdk/blob/main/1-ModAPI/%E4%BA%8B%E4%BB%B6/%E4%B8%96%E7%95%8C.md#serverchatevent)。原生图片操作参考 [UI 控件 Rotate](https://github.com/MCNeteaseDevs/mc-netease-sdk/blob/main/1-ModAPI/%E6%8E%A5%E5%8F%A3/%E8%87%AA%E5%AE%9A%E4%B9%89UI/UI%E6%8E%A7%E4%BB%B6.md#rotate) 和同页的 SetSize、SetTextColor。聊天反馈使用 Msg 组件的 [NotifyOneMessage](https://github.com/MCNeteaseDevs/mc-netease-sdk/blob/main/1-ModAPI/%E6%8E%A5%E5%8F%A3/%E4%B8%96%E7%95%8C/%E6%B6%88%E6%81%AF.md#notifyonemessage)。

离线测试覆盖表单构建、指令分发、回调、动画几何和关闭后停止更新；实际游戏中的渲染、触摸操作及跨端时序仍需在网易客户端按上表检查。
