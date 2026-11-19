# 先见一步 · 当前主报告 V5 Beta

负责人在 2026-11-19 明确“报告以 V5 Beta 版本为准”。本版共 **11 页，7,693,920 字节**，来自当天最新上传的原文件。

[在线逐页阅读](https://codezzzsleep.github.io/next-zenith-beforestep/report.html) · [当前 PDF](report.pdf) · [原上传文件](../先见一步_项目报告书_v5_beta.pdf) · [逐页图与来源清单](manifest.json)。

源提交为 `33d7dfe1ce1a43c5ea6cc3f72f8b2ec5fb509511`，本目录与网站 PDF 都按原字节复制，SHA-256 相同：

```text
fe2ff9b9356202760254cc29deadfa1e963986d69c7c0f1ee39b9ab0764d1cb7
```

报告的封面使用作者选取的较亮 M20 探索截图。README 的新机器人配图直接提取该原截图并另存展示裁图，原 PDF 未改写。配图与重建说明见 [亮图资产](../../docs/readme/m20-bright-20261119/README.md)。

原稿的 467 个任务是归档节点；当前累计账本为 491 创建 / 460 成功 GLB / 31 失败。原研究、当前游戏局数、录制秒数分别识别，当前操作与原片见 [当前交付](../../docs/current-status.md)。原 V5/V4/V3 与早期 Beta 上传继续留档。

重制阅读图使用 [render_reader.py](render_reader.py)：

```sh
python reports/v5-beta/render_reader.py --source reports/先见一步_项目报告书_v5_beta.pdf --repo .
```

脚本只核对原件与完整渲染页面，使用 PyMuPDF、Pillow，不生成或改写报告内容。
