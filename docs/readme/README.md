# README 图文与来源

当前 README 恢复照片到模型的动态展示、完整流程、模型与行动对照及六个核心版本的资产比较，并保留 V5、当前试玩与原片入口。视觉沿用纸白、暖灰、深蓝与金色；桌面和窄屏使用同一组真实来源。

2026-11-19 改稿将“空间前额叶 + 轮腿”的双线叙事、GitHub 原生 Mermaid 与实证总表放在主阅读流程，真实四步拼版在展开项中继续保留。[本轮来源核查](../narrative-evidence-20261119.md)记录官方训练表述、每组实验的适用范围和 491/467 两个统计节点。

原 GIF、原模型/行动截图、历史拼版及三张 R1 证据图的字节保持。新版排版另存于 [showcase/](showcase/)，来源和产物 SHA 见[当前图文清单](showcase/sources.json)。历史图文的[原清单](sources.json)继续保存，清单中的当时首页状态按其历史身份阅读。

## 当前正文使用的图文

| 图文 | 内容与来源 |
| --- | --- |
| [photo-to-model.gif](photo-to-model.gif) | 原照片到对应 Lux3D 模型的动态片段；R1 研究 / Go2W |
| [桌面流程](showcase/flow-desktop.png) · [手机流程](showcase/flow-mobile.png) | 原 RGB、真实三维候选、完整十二世界与原场景独立行动 |
| [桌面模型/行动](showcase/model-action-desktop.jpg) · [手机模型/行动](showcase/model-action-mobile.jpg) | 官方 Aholo Viewer 原模型截图与原 R1 行动截图，均完整保留 16:9 |
| [桌面六版本](showcase/versions-desktop.png) · [手机六版本](showcase/versions-mobile.png) | V6、V7、V8、v0.1、v0.2、v0.3 的完整模型/输入矩形，桌面三列、手机两列 |
| [试玩轮腿帧](../../evidence/judges-demo/figures/05-M20-leg-action.jpg) | 2026-11-18 连续母片中的逐腿操作；M20 显示外观 |
| [三张原 R1 证据图](../../site/media/home-evidence-20261118/sources.json) | 可见面核对、完整四乘三十二世界、三策略独立终态；在正文证据展开项中保留 |

### 照片、模型与行动

GIF 来自 `evidence/lux3d-demo-v2/BeforeStep-Lux3D-Demo-v2.mp4` 的 4.1–11.9 秒片段，8 fps，62 帧；源提交为 `ab537d62c075c4d7be1e829cecb69a4708258221`。GIF SHA 与[原来源清单](sources.json)一致，没有重新剪辑。

新流程的照片与模型对应真实任务 **5958685**。模型/行动双图分别使用保留的 [viewer.jpg](viewer.jpg) 与 [robot-action.jpg](robot-action.jpg)，取自同一原影片的第 35 秒与第 84 秒，使用 Go2W 条件。拼版只完整适配原图，保持各自的画幅比例。

### 完整十二世界

流程第三格使用[当前十二世界证据图](../../site/media/home-evidence-20261118/02-twelve-world-rehearsals.jpg)中完整的视频矩形 `[176, 127, 1424, 829]`。提取只去除该拼版后来添加的纸白标题和页脚，四乘三十二格全部保留；上游为 `s05-world-grid.mp4` 第 3 秒。

原[三图来源清单](../../site/media/home-evidence-20261118/sources.json)保留视频 SHA、布局与时间码。历史 [model-to-decision.png](model-to-decision.png) 的第三格是原九格节选，继续留档；当前正文流程已使用完整十二世界。

### 六个核心版本

新排版从保留的 [asset-iterations.png](asset-iterations.png) 提取六个完整模型/输入矩形，统一等比适配，不重新绘制几何、不单独放大模型。矩形坐标、原图 SHA 与上游图文构建来源在[当前清单](showcase/sources.json)和[原清单](sources.json)中分别记录。

V6 是观测约束融合结果；v0.1 代表真实两图重试的被拒模型，两个原输入都保留；其余各版本的真实模型、输入、任务与冻结配置见[核心资产清单](../../evidence/award/asset-iterations/manifest.json)。报告 V5 与技术版本分别编号，图片不把所有版本概括成生成成功或执行成功。

### 当前试玩原片

正文的 M20 轮腿图直接复用 `05-M20-leg-action.jpg`，源母片为 `00-full-run.mp4`，代码版本 `d6397c5273aa050a4987e4f42c0a5e54dfff40a3`，视频时间约 **216.368 秒**。完整画幅与原 JPEG SHA 保持；[原素材清单](../../evidence/judges-demo/manifest.json)记录对应状态与原 PNG。

这张图显示跨越过程中的一个动作。完整两世界预演、四腿 12 个主要动作与到达属于[整局验收](../../docs/judges-demo.md)。当前文档与报告入口为 V5，录制帧中的界面文字保持所拍版本。

## 重制当前响应式拼版

[build_showcase.py](build_showcase.py)只读取保留图片、核对 SHA，再做等比适配和排版。需要 Pillow 与 CJK 字体，不运行仿真、不调用生成服务。使用一份新输出目录：

```sh
python docs/readme/build_showcase.py \
  --repo . --out outputs/readme-showcase \
  --sans /path/to/NotoSansCJKsc-Bold.otf \
  --serif /path/to/NotoSerifCJKsc-Bold.otf
```

`--source-root` 可以指定另一份含真实二进制图片的本地工作副本。脚本拒绝已有输出目录，并记录字体与每张新图的 SHA；字体来源与许可证见[致谢](../credits.md)。重建需要的图片均为本库保留的 README 与展示图，不要求重新下载原长影片。

README 使用 GitHub 支持的 `picture / source`，在 `max-width: 600px` 时选择窄屏版本；图片以自然比例显示。原图可通过来源链接查看，详细操作和科学结论仍使用正文文字提供。

## 保留的其他构建器

[build_evidence_panels.py](build_evidence_panels.py)是首页三张原证据图的构建工具，其原观测、视频与来源清单保持。它需要 Pillow、ffmpeg 与 CJK 字体：

```sh
python docs/readme/build_evidence_panels.py \
  --repo . --world-grid evidence/production-v6/shots/s05-world-grid.mp4 \
  --font /path/to/NotoSansCJKsc-Bold.otf
```

历史 [build_assets.py](build_assets.py)生成最初的 GIF、四步流程、截图与六版拼版，依赖其 SHA 固定的原影片及原六版本大图。重制时选择独立输出目录，按各构建器原来源核对；原资产与当前首页图不会被新拼版覆盖。
