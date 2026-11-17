# 报告资料出处

本报告更新作品说明，复用仓库已有记录与素材。所有结果为 MuJoCo 仿真；原 R1/R2/R3 实验、后验修订、展示路线与浏览器游玩分别说明，不能合并成总体成功率。报告制作没有新增 Lux3D 调用、训练或研究实验。

| 报告内容 | 已有出处与口径 |
|---|---|
| 491 次创建 / 460 成功返回 / 31 失败 | `evidence/production-v6/facts.json` 的 `lux.live_ledger_counts`；该文件另保留早期 467/438/29 基线，不混计 |
| 306 陈列模型 / 110 采纳 / 196 拒绝 | `site/data/gallery.json` 的 `stats` 与完整 `models`；陈列数是可查看子集，不能称为全部460份 |
| R1 一眼到达 112.84 s / 乐观碰撞 80.87 s / 保守5眼停止 | 同一 facts 文件的 `r1`；字段保留原 summary 的路径、SHA与JSON指针 |
| 6 份A、B创建6次一失败、2份通过、12组合 | 原V3第3/4页，`docs/report.md` 与 `docs/mission-verification.json`；游戏沿用11份真实返回、8采纳 |
| 轮行 0/90 与腿跨越 24/24 | facts 的 `legs`，指向 `evidence/crossing/calibration/gate.json`；离散10/12/15 cm的能力带，不推成所有岩石的通用能力 |
| 强信被拒候选 17/102 碰撞 | `evidence/suite/summary.json` 的 `counterfactuals.executed/collisions`，不是306陈列模型的统计 |
| 64份采纳候选中23份背面短超过5 cm | facts 的 `back_error`，指向 R3 `back-error/stats.json` |
| 8个决定性场景3达/3停/2碰 | facts 的 `decisive_eight` 与 suite summary；前两基线0到达由挑选条件决定，不能作随机成功率 |
| R3后验修订17场景零碰撞 | facts 的 `post_result_v3`；已知12场与留出5场，规则看过结果后收紧，只作参考 |
| 同路5场景的腿必要与Lux边界 | 原V3第7/8页与 facts 的 `same_route`；不能将两条腿必要例子当成Lux普遍必要证明 |
| 53次低石生成、7采纳、29全拒/24中7通过与191秒跨越 | 原V3第6/8页及 `evidence/crossing/` 保留记录；开发示例不是新的预注册检验 |
| 同路独立验证的12/12世界、56.34 s碰高石、174.258 s终态 | `docs/mission-verification.json` 的 `worlds`、`optimistic`、`finish`；属于展示任务的软件物理检查，沿用原记录 |
| 门槛前纯轮行60秒未过线 | 同一文件 `wheelOnly`；它从门槛前开始，不能与56/174秒累计仿真时钟作速度横比 |
| 11.9 cm门槛 | 同一文件 `scan`；来自当前可见门槛几何，未经过Lux3D生成 |
| 当前游戏默认两模型世界、最多12组合、强制看模型后释放手控 | `docs/mission.md`、`evidence/showcase-guided-20261116/README.md` 与 `site/mission-showcase.js`；手控释放不等于预演认证 |
| 四腿12个主要动作与16执行器 | `docs/mission.md`、`docs/mission-verification.json` 与原Go2W资源；重心和支撑准备由控制器辅助 |
| 新版完整录像332.96秒（展示约5分33秒） | `evidence/showcase-guided-20261116/BeforeStep-guided-mission.mp4` 与同目录manifest/README；默认两世界，不能把旧28分33秒键盘片当成本轮 |
| 首页185秒/配乐Demo157秒 | `site/index.html` 的作品播放器标记与 `evidence/lux3d-demo-v2/README.md`；是两份不同影片 |

`facts-snapshot.json` 留下本版引用的已发布数值和源文件SHA，供读者按原记录查验。它不替代仓库里的任务输入、模型、失败与执行文件。`asset-sources.json` 给出38件报告素材的实际来源、输入SHA、任务身份与必要的裁图/抽帧方法；新跨腿图从已有录像270秒取一帧。

`inventory.json` 和 `content-map.json` 将原V3的293个抽取片段合并为110个经审阅的语义单元，逐项指向新正文；21个原始显示裁图保存在 `source-assets/`。V3原文件位于 `site/media/report.pdf`，SHA `67c15f4af8c02c79c4254e55774207acf51796784583e58543c5d482c0199cc6`。自动引用覆盖不证明改写语义，最终成稿须另外逐页核对。

字体来源与SIL OFL许可见 `fonts/sources.json`、`fonts/OFL.txt`。PDF引擎来自用户提供的 `project-report-pdf-v2-afterclaude-gpt.zip`；engine内39个文件保持输入ZIP的原字节，源ZIP SHA `26b86cf54bf544d1e0fe55fd94a19fd285d5ccb4b42e30acac49b99406782a4a`。
