# 使用 FormUI Skill

本项目附带 `netease-formui` skill，指导 AI 按 FormUI 的公开接口编写网易版《我的世界》表单。它覆盖客户端与服务端用法、Observable 数据绑定、OreUI / Flutter / Fluent 风格、Group 组合控件，以及 Custom 原生 UI 操作和动画。

Skill 主要指导调用库制作表单，遇到不明确的业务需求或初始化约定时会询问使用者。它提供指令与参考资料，游戏中无需加载这些文件。

## 在本项目中使用

1. 克隆或下载完整仓库，保留根目录下的 `.agents` 文件夹。
2. 在 Codex 中打开项目目录；使用 CLI 时，从项目目录或其子目录启动。
3. 在对话中显式指定 skill，再描述希望实现的功能：

   ```text
   使用 $netease-formui 编写一个服务端设置表单。
   使用 Fluent 风格，包含音量滑动条、音效开关和保存按钮。
   只显示给触发操作的玩家，每个玩家的设置独立保存。
   请接入项目已有的事件入口。
   ```

Codex 会从仓库内的 `.agents/skills` 发现技能，因此随项目使用时无需另行全局安装。它也可以根据任务描述自动选择 skill；希望明确使用此 skill 时，直接在提示中写 `$netease-formui`。如技能未出现，可重启 Codex 后再次检查。发现规则和调用方式见 [OpenAI 官方技能教程](https://learn.chatgpt.com/docs/build-skills)。

使用其他 AI 编程工具时，先确认它支持 Agent Skills，并按照该工具的规则配置技能位置。本教程以 Codex 为例。

## 在自己的模组项目中使用

将本项目中的整个 `.agents/skills/netease-formui` 文件夹复制到目标项目的 `.agents/skills/`，保留如下结构：

```text
你的模组项目/
└── .agents/
    └── skills/
        └── netease-formui/
            ├── SKILL.md
            ├── agents/
            │   └── openai.yaml
            └── references/
                ├── forms.md
                └── composition.md
```

同时为目标模组接入 FormUI 行为脚本、资源包和系统初始化。复制 skill 只会添加 AI 的调用指导，不会自动安装游戏侧依赖。接入 UI 资源时合并目标项目的 `ui/_ui_defs.json`，并保留所用模板引用的纹理和元数据。

Skill 会依据目标项目实际的库位置和导入路径查找 FormUI；找不到时会询问位置。建议同时保留所用版本的 FormUI 文档，或向 AI 提供完整 FormUI 仓库的位置。复制的 skill 不会随源仓库自动更新，升级库时应一并更新技能文件及参考资料。

不需要全局安装也能在自己的模组中使用。若希望让同一台机器的多个项目都能发现它，可放到当前 Codex 官方文档规定的个人目录 `~/.agents/skills/netease-formui/`；Windows 的 `~` 通常是用户主目录。个人目录里的 skill 仍需要访问目标项目实际使用的 FormUI 库。[技能作用范围说明](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)

## 怎样描述需求

尽量说明以下信息，已有代码能确认的部分可以由 AI 自行读取：

- **运行端与目标玩家**：客户端本地展示，还是服务端向指定玩家或多人展示。
- **状态范围**：每个玩家独立，还是多个玩家共享同一份状态。
- **风格和布局**：OreUI、Flutter 或 Fluent，浅色或深色，列数、尺寸和位移。
- **交互和入口**：按钮行为、输入绑定、触发事件、关闭与重新打开的要求。
- **交付方式**：直接给出示例，或修改目标项目中的业务文件。

例如，只想阅读示例时：

```text
使用 $netease-formui 给出一个客户端 Group 示例。
组内有一个标题和两个按钮，宽度通过 Observable 更新，
按钮点击后更新标题。不要写入文件。
```

需要原生动画时：

```text
使用 $netease-formui 制作一个 Custom 控件，引用现有的图片模板。
图片每帧旋转 2 度，用 Observable 保存角度，按钮控制开始和暂停。
关闭后停止更新，重开后为新实例重新绑定。
请先检查项目里的模板子路径，缺少资源定义时向我确认。
```

## 开源分发与验证

发布项目时，将 `.agents/skills/netease-formui/`、本教程及 README 中的入口一起提交到仓库；制作源码压缩包时确认包含 `.agents`。技能目录没有个人机器绝对路径，适合随项目分享。

使用者仍需在网易客户端验证渲染、输入、关闭与重开，以及多人场景下的同步行为。Skill 和离线测试不能替代真实游戏验证。

如库的公开接口发生变化，应同步维护 `SKILL.md`、参考文件和示例，确保技能与所分发的库版本一致。
