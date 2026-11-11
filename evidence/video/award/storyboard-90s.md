# 90 秒分镜

每镜均取真实记录；视频由负责人录屏、渲染与剪辑。字幕数字来自 `evidence/award/facts.json` 和原失败证据，不从旧视频沿用结论。

| 镜号 | 时长 | 画面 | 来源文件 | 字幕 | 负责人录屏 |
| --- | --- | --- | --- | --- | --- |
| 1 | 8s | 一张真实照片进入 Lux3D：显示实际上传 JPEG 与同任务生成的整块石头，镜头停在照片和模型之间；录制首页成品或技术报告真实模型查看器。 | `evidence/web-assets/models/5958685.glb; evidence/web-assets/objects/36c6920301bb5aee1a23970af7b9229a100ee42ffb0aa70f9e84edd61c2aa5cd.jpg; evidence/web-assets/anchor.json; site/report.html#assets` | 机器人只拍到一面。Lux3D 把这一张照片变成一整块石头。 | 是 |
| 2 | 12s | 为什么非想背面不可：用真实首眼 RGB 与静态 DARK 对照交代低角度太阳，再显示三车原轨迹；不做影子拖动动画。 | `evidence/video/award/first.png; evidence/web-assets/observations/conservative-look1-dark.png; site/data/demo.json` | 背光面全黑，车却要从看不见的那一面旁边过。保守停车，乐观碰撞，原 Lux 到达。 | 是 |
| 3 | 18s | 高潮：整块石头，转到背面：在真实模型查看器拖动原任务石头至背面，显示同一照片的多份模型与任务 ID；真值叠合只用提供的配准矩阵，未接好时录制真实独立模型与原背面诊断。 | `evidence/web-assets/models/5958685.glb; evidence/web-assets/objects/36c6920301bb5aee1a23970af7b9229a100ee42ffb0aa70f9e84edd61c2aa5cd.jpg; evidence/web-assets/models.json; evidence/web-assets/registrations.json; evidence/web-assets/truth/B.glb; site/report.html#assets` | 这一面，照片从没拍到，是 Lux3D 想出来的。锚点三维间隙 47.541 mm，二维包络间隙 0 mm，成功不稳健。 | 是 |
| 4 | 14s | 想象怎样接受检查：展示通过与被拒的真实候选及原因，配准叠回观测，再展示十二份完整预演轨迹；录制技术报告与对应终端记录。 | `evidence/web-assets/registrations.json; evidence/web-assets/anchor.json; site/report.html#award-lux-pipeline; evidence/video/index.json` | 原批 166 份 GLB，64 准入、102 拒绝；被拒干预 17/102 会撞。 | 是 |
| 5 | 12s | 真实执行与三车结果：负责人录制零付费 --reuse-lux 的终端真实观察、自检、预演、执行；同时录制原三车真实回放。无头运行没有窗口，网站回放另开 8081。 | `ops/award_record_screen.py; evidence/reviews/beforestep_r1/lux/original_b/traj.npz; evidence/video/award/award-final-local-choices.png; site/data/demo.json` | 已知决定性 8 场：原想象 3 到达、3 停车、2 碰撞。 | 是 |
| 6 | 10s | 两次真实碰撞及原因：先显示 F1_020 被完全遮住的 C，再显示 F3_004 通过正面自检但偏短的 B 背面；锚点间隙同时呈现。 | `evidence/video/award/award-final-local-failures.png; outputs/suite/real/suite_r2_v4_F1_020/imagination; outputs/suite/real/suite_r2_v4_F3_004/imagination; evidence/reviews/beforestep_r3/failure-facts.json` | F1_020：C 从未被看见；F3_004：背面偏短。锚点三维间隙 47.541 mm，二维包络间隙 0 mm，成功不稳健。 | 是 |
| 7 | 10s | 赛后修订与适用范围：展示五栏表、留出单独成表，oldv2 碰撞保持可见；停下不当作效率优势。 | `evidence/video/award/award-final-local-revision.png; evidence/reviews/beforestep_r3/summary.json` | 样本外：原想象 1 到达、2 停车、2 碰撞；最终 v3 修订 0 到达、5 停车、0 碰撞。有效，但不绝对。oldv2 曾在 F1_003 碰撞。 | 是 |
| 8 | 6s | 证据与入口：显示真实资产迭代图、仓库、可体验网页、报告 PDF；新演示若执行加上不参与结论标注。 | `evidence/video/award/asset-iterations.png; docs/hackathon-submission.md; site/en.html` | 原结果、失败、输入、生成资产与源码都公开。赛后补充演示不参与结论、不作为泛化证据。 | 是 |
