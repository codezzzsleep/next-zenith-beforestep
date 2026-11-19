# 先见一步 · 历史项目报告 V5

当前主报告已按作者新要求切换为 [V5 Beta](../v5-beta/README.md)。本目录的原 V5 PDF 与历史阅读图保持原字节。旧重制脚本属于历史构建记录；当前主报告使用 `reports/v5-beta/render_reader.py`。

这是负责人在 2026-11-18 指定的历史 V5 报告：**11 页，6,730,562 字节**。

[逐页阅读](https://codezzzsleep.github.io/next-zenith-beforestep/report.html) · [原 PDF](report.pdf) · [逐页图与来源清单](manifest.json)。

原文件由负责人上传至 `main` 的提交 `4cf7ebd14cfc4d560972ab042b38a929287cd01e`，路径为 [reports/v4/先见一步_项目报告书_v5.pdf](../v4/先见一步_项目报告书_v5.pdf)。上传原件继续保留，本目录与网站 PDF 均按原字节复制，SHA-256 相同：

```text
fd4327db258db4874be97dc96668362bb540db2a3978d3f82717864bbcaab9f9
```

## 原稿与当前运行的范围

原稿中的 467 创建 / 438 成功是明确的归档节点；当前保留的累计账本为 491 创建 / 460 成功 / 31 失败，见 [facts.json](../../evidence/production-v6/facts.json)。当前公开介绍使用“累计 491 个真实任务（V5 Beta 归档 467 个）”，不把两个节点混成新的生成。

报告第 10 页保留了游戏的阶段截图与当时说明。当前版本始终显示完整原材质，在自然遮挡下先记录初判，再自选手控、想象、补看或停车；预演许可只约束辅助路线。2026-11-18 连续母片、清楚的模型/地图补拍、停车与五图已另行交付。现行玩法和素材见[月面任务](../../docs/mission.md)、[当前状态](../../docs/current-status.md)及[原片索引](../../evidence/judges-demo/README.md)。

原 PDF 不因这些配套说明改写。原 R1 的十二世界、当前评审局的两个世界、研究结果与游戏积分分别保持身份。V3/V4 历史原件见[版本索引](../README.md)。

## 重制阅读图

[render_reader.py](render_reader.py)核对原 PDF SHA，完整渲染各页为 1200px 宽 JPEG，并产生报告阅读页和来源清单。使用 PyMuPDF 与 Pillow，不重新生成或修改报告正文。

```sh
python reports/v5/render_reader.py --source reports/v5/report.pdf --repo .
```

网站 `report.html` 与 `project-report.html` 现指向 V5 Beta；本目录仍保留历史 V5；旧的 `media/report.pdf` 和 `report-v3.html` 明确保留为 V3 历史入口。
