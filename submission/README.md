# 参赛材料入口

队伍：Next Zenith；作品：先见一步。主体验是浏览器中的月面轮腿任务：观察高石、转看已有真实 Lux3D 模型、在模型世界中试路、实际绕行、亲手跨越门槛并抵达。探索检查点、全程挑战、勘察印记和个人纪录增加可玩性；成绩独立于原科学实验。

按作者2026-11-17的决定，**主报告仍为 V3，主宣传采用作者已经上传的 B站视频**；V4 与完整实验影片保留为补充资料。

```text
https://b23.tv/4CAPaLu
https://codezzzsleep.github.io/next-zenith-beforestep/play.html
```

| 材料 | 本仓库位置 |
| --- | --- |
| 主报告 V3 | `site/media/report.pdf`、`site/report.html` |
| B站主宣传视频 | 作者已发布，BV1aYsw6REh7；上方分享链接 |
| 可操作主任务 | `site/play.html`、`docs/mission.md`、`docs/playability.md` |
| 本轮可玩性验证 | `evidence/playability-20261117/verification.json` 与实际截图 |
| 完整实验影片与旧 Demo | `evidence/lux3d-demo-v2`、`evidence/production-v6`，原文件保留 |
| V4 补充报告与构建源 | `reports/v4`，不替代作者指定的主报告 |
| 源代码（按必交交付） | 本仓库、`src/beforestep`、`setup.sh`、`tests` |
| 关键资产与迭代对比 | `assets/manifest.json`、`docs/milestones.md`、`site/media/*comparison.jpg` |
| 原科学运行证据 | `evidence/reviews/beforestep_r1`、`evidence/suite`、`evidence/reviews/beforestep_r3` |
| 实际训练模型与物理示教 | `assets/models/goal_controller_v4`、`assets/training/goal_controller_v4`、`evidence/training` |
| 模型任务和失败回放 | `site/learning.html`、`site/media/learning-demo.mp4`、`evidence/learning` |
| 历史生成实验 | `experiments/trained_live_gate_001`、`experiments/gate_passage_001`、`experiments/polar_retry_001`；本轮没有新生成 |
| 独立通行验收 | `evidence/scenes/gate_passage_001/validation.json` 与 `trials/*.jsonl` |
| 小红书传播文案 | `xiaohongshu.md`，发布后附公开链接和 #Aholo黑客松 |

v0.3 的已训练控制器及实时 Lux3D 关口闭环仍按原证据保留，用于技术迭代对比；主科学口径以冻结的 R1/R2/R3 结果为准。候选核对和预演通过不能保证未知背面正确，机器人为 MuJoCo 仿真。

B站主宣传片已由作者发布。最终官网报名、组队与提交由参赛负责人执行；本次代码及入口更新不代替官网提交。
