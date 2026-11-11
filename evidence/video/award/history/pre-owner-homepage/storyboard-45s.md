# 45 秒分镜

每镜均取真实记录；视频由负责人录屏、渲染与剪辑。字幕数字来自 `evidence/award/facts.json` 和原失败证据，不从旧视频沿用结论。

| 镜号 | 时长 | 画面 | 来源文件 | 字幕 | 负责人录屏 |
| --- | --- | --- | --- | --- | --- |
| 1 | 4s | 真实机器人运行：负责人用零付费命令录制 MuJoCo 被动查看器的真实独立执行与旁边的网站。 | `ops/award_record_screen.py; evidence/video/index.json; evidence/reviews/beforestep_r1/lux/original_b/traj.npz` | 看不见的那一面，先在想象里走一遍。 | 是 |
| 2 | 6s | 两种影子：固定首眼太阳黑影参考，拖动到真实第二眼，地图随原观测变化。 | `evidence/video/award/first.png; evidence/video/award/second.png; site/data/award-observations.json` | 太阳照不到的地方，换位置也照不亮；视线遮挡，换一个真实位置再看。 | 是 |
| 3 | 8s | 三种选择与测深对照：并排真实轨迹，揭晓保守、乐观、Lux 与 see-dark 原终态。 | `evidence/video/award/award-final-local-choices.png; site/data/demo.json` | 原窄道：保守停车，乐观碰撞，真实 Lux 到达；黑影测深对照也到达。 | 是 |
| 4 | 5s | Lux3D 核心链：转动真实候选，展示配准、自检、候选完整预演与独立执行。 | `site/index.html#award-lux-pipeline; evidence/award/facts.json; evidence/video/index.json` | 原批 180 个唯一任务，166 份 GLB；64 准入，102 拒绝。 | 是 |
| 5 | 7s | 两次真实碰撞及原因：先显示 F1_020 被完全遮住的 C，再显示 F3_004 通过正面自检但偏短的 B 背面；锚点间隙同时呈现。 | `evidence/video/award/award-final-local-failures.png; outputs/suite/real/suite_r2_v4_F1_020/imagination; outputs/suite/real/suite_r2_v4_F3_004/imagination; evidence/reviews/beforestep_r3/failure-facts.json` | F1_020：C 从未被看见；F3_004：背面偏短。锚点三维间隙47.541 mm，二维包络间隙0 mm，成功不稳健。 | 是 |
| 6 | 6s | 赛后修订与适用范围：展示五栏表、留出单独成表，oldv2 碰撞保持可见；停下不当作效率优势。 | `evidence/video/award/award-final-local-revision.png; evidence/reviews/beforestep_r3/summary.json` | 想象只解释太阳的影子；视线的影子，再看一眼。最终 v3 已知场景：3到达、9停车、0碰撞；指定留出：0到达、5停车、0碰撞。 oldv2 曾在F1_003碰撞。 | 是 |
| 7 | 5s | 被拒候选的反事实：回放原批被拒干预，展示完整前缀核验；修订批按已知与留出分开。 | `site/index.html#counterfactual; evidence/suite/summary.json; evidence/award/facts.json; evidence/video/index.json` | 原批被拒干预 17/102 碰撞；修订已知批 17 份另列。 | 是 |
| 8 | 4s | 证据与入口：显示真实资产迭代图、仓库、可体验网页、报告 PDF；新演示若执行加上不参与结论标注。 | `evidence/video/award/asset-iterations.png; docs/hackathon-submission.md; site/en.html` | 原结果、失败、输入、生成资产与源码都公开。赛后补充演示不参与结论、不作为泛化证据。 | 是 |
