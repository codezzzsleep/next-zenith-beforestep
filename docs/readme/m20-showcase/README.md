# M20 展示素材与原始证据

当前 README 与网站使用保留的 M20 连续录制、模型对比补拍及停车分支制作展示素材，未创建新的 Lux3D 任务。原片身份与逐文件 SHA 见 [sources.json](sources.json)，网站媒体身份见 [网站来源清单](../../../site/media/m20-showcase/sources.json)。

原片来自 [judges-demo-20261118 固定下载](https://github.com/codezzzsleep/next-zenith-beforestep/releases/tag/judges-demo-20261118)。脚本核对母片、模型对比片与停车片的完整 SHA，截取观察 11.5 秒、探索 290 秒和轮腿 216.368 秒；展示裁图为原 1920×1080 画面的 `(350,125,1550,800)`，保持 16:9，原文件不变。

[build_m20_showcase.py](../build_m20_showcase.py) 接收 `--source` 仓库目录、`--out` 输出目录、`--mother` 母片、`--comparison` 模型对比片、`--hold` 停车片和 `--fonts` 字体目录。字体使用 Noto Sans CJK SC Bold 与 Noto Serif CJK SC Bold；`--images-only` 可重新导出 GIF、图片与拼版，保留已生成视频。完整执行另生成 185 秒演示及六个原速片段，剪辑区间和速度写入来源清单。

GIF 使用原任务 5958685 的输入照片与已有 Aholo Viewer 旋转帧。六版本图保留原模型和输入。十二格由原六份 A、两份 B 候选组成，完整预演通过后用现有 M20 外观绘制，各任务身份在网站来源清单中。

M20 为当前显示外观，研究的 Go2W 动力学、控制、输入、原始 GLB、R1/R2/R3 结果及 V3/V4/V5 报告均保持原身份。当前演示的剪辑时长、游戏结果和历史实验时钟分别记录；历史页面原文保留在 [docs/history/site](../../history/site/)。

[本地视觉与交互验收](verification.json)记录两种屏宽、明暗背景、加载/故障与回放检查；手机真机性能仍以当前项目说明的范围为准。
