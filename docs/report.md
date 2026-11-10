# 先见一步：看不见的那一面，先走一遍

Next Zenith · 负责人 R1 主线复核 · Aholo Lux3D。主实验源码 `2147b2f`；完整结果与逐次原始 summary 见 [R1 执行记录](reviews/RESULT_BEFORESTEP_R1.md)。

## 两种影子，一个行动问题

太阳照不到的地方没有可靠深度；岩石挡住的地方也看不见。机器人沿月溪和大石堆之间的窄道前进，A 挡在前面，B 的一部分藏在盲区。第二次观察能改变视线遮挡，却不能照亮太阳黑影。系统让 Lux3D 提出符合可见观测的几何假设，检验路线后再行动。

![第一眼画面与两种未知](../site/media/r1-shadows.png)

## 窄道的约束

月溪与大石堆构成禁行边界，A遮住前方空间，B后半截凸进必须换道的通路。

## 三台车的实际结果

主场景保留 stress_v8 的 A+B、太阳、起点、第一眼和终点 `(10.5,0)`；所有主对比统一规则控制。保守车看五眼仍没有路线；只让相机在黑影里也有深度，三眼到达。乐观车碰撞，其出发前原计划车身压入真实 B 21.899 cm，满足原要求的至少 10 cm。真实 Lux3D 分支一眼到达，12 个候选组合预演全部完成且无碰撞，独立执行也无碰撞。

| 运行 | 结果 | 观察次数 | 仿真总时长 | 证据 |
| --- | --- | --- | --- | --- |
| 看清再走 | 无路线、停车 | 5 | 142.2 s | [原始身份](../evidence/reviews/beforestep_r1/section25_final_base/conservative/run_identity.json) |
| 黑影测深对照 | 到达 | 3 | 147.26 s | [原始身份](../evidence/reviews/beforestep_r1/section25_final_base/see_dark/run_identity.json) |
| 直接走 | 碰撞 | 1 | 80.87 s | [原始身份](../evidence/reviews/beforestep_r1/section25_final_base/optimistic/run_identity.json) |
| 想一想再走 | 到达 | 1 | 112.84 s | [原始身份](../evidence/reviews/beforestep_r1/lux/original_b/run_identity.json) |
| 真实形状检验 | 到达 | 1 | 115.88 s | [原始身份](../evidence/reviews/beforestep_r1/section25_final_base/truth/run_identity.json) |

![三种策略的实际轨迹](../site/media/r1-routes.png)

这些结果支持在本次冻结场景中生成几何对行动判断的作用；不宣称对任意石头或场景都可靠。地图上的扫描轮廓只用于赛后复盘，生产规划器不读取隐藏真值。

## 真实生成、自检与被拒候选

首眼共提交 12 个独立真实任务，获得 11 个 GLB、1 个服务端失败。A 的六份全部准入；B 的五个可用模型中两份准入、三份拒绝。B2 任务 `5958893` 失败，无 GLB；不能将它计为自检拒绝。所有原始输入、实际上传字节、任务身份、模型、矩阵和占据保留在 [完整实验数据](../evidence/reviews/beforestep_r1/lux/original_b)。

| 候选 | 真实 task ID | 轮廓 IoU | 尺度比 | 冻结自检 |
| --- | --- | --- | --- | --- |
| B/A1 | 5958642 | 0.4325 | 1.0676 | 轮廓 IoU 低于 0.7068 |
| B/A2 | 5958654 | 0.8459 | 1.0 | 准入 |
| B/B1 | 5958703 | 0.2715 | 0.9324 | 轮廓 IoU 低于 0.7068 |
| B/C1 | 5958934 | 0.7108 | 0.9459 | 准入 |
| B/C2 | 5958937 | 0.63 | 0.9054 | 轮廓 IoU 低于 0.7068 |

![B 的冻结轮廓检查](../site/media/r1-self-check.png)

轮廓门槛 0.7068、尺度比 0.889–1.09、壳层接触、已知自由空间侵入和未知比例等原门槛保持。准入表示符合当前可见观测，生成背面仍可能错误：两份准入 B 的后缘相对真实占据分别偏短 0.70 m、0.60 m。此次行动结果通过，不把它说成生成背面已准确。

## 第二眼的条件分支与配准修复

需要补看时，用目标可见高度、相机到最近观测格的距离和原图焦距估计像素高度；排除过近点，优先可达的 ≥512 px 点。两眼 native_ok 同时为真才调用两图三份，否则单用新视角六份；第二眼零准入仅追加同字节六份，合计十二仍零则停车，不看第三眼。

![真实首眼与独立替身的第二眼输入](../site/media/r1-observation.png)

本次真实B首眼251 px、native_ok=false，仍有A2和C1两份准入。独立完整替身验证中，第二眼预计513.388 px，实际506 px，仍按单图分支。发现局部配准优化的稀疏点评分变好、最终可见面评分反而退化；修复只保留最终评分更好的矩阵。原自检与余量没有放宽，B替身修复后IoU为0.9673，完整两眼预演与执行到达。40 项单测通过。本次真实主线首眼已有准入和路线，第二眼、追加与 B 替换均未触发；不冒称做了新的多轮 Lux 生成。

## 在想象中预演，然后在独立世界执行

规划使用全部八份准入几何的占据；执行前，在 A 六份 × B 两份共十二种物理场景中完整运行同一规则控制器。十二格均完成、无碰撞，其全部轨迹与原配置在仓库。之后在独立扫描几何世界执行，实际到达。完整 `--reuse-lux` 重放再次完成十二格与独立执行，t、qpos、阶段和动作来源等全部数组逐字节相同，轨迹 SHA256 为 `6b1481752708b9a2c9039ad91e55f98493714924afdd52da1be0baaee4758d1e`。

## 赛后真值与间隙复盘

按每一个保存 qpos 重建原 MuJoCo 可碰撞几何，其最小有符号距离为 A 256.109 mm、B 47.541 mm，均为正，与执行无碰撞相容。XY 的 0.76×0.66 m 矩形包络对 B 间隙为零，中心距离减半车宽最小为 -62.778 mm；这是平面包络指标，同时公开（中心减半宽=-0.062778 m），不当作三维接触。原规划始终遵循冻结的 5 cm 占据扩张规则；不将 47.541 mm 向上写成真实 5 cm。

![真实可碰撞几何的最小距离](../site/media/r1-clearance.png)

原运行墙钟 1223.6 s，含冷配准和完整物理预演，不含此前云端排队，不能称为端到端延迟；仿真总时长与执行时间分别记录在summary。

原始 [eval](../evidence/reviews/beforestep_r1/lux/original_b/eval.json)、[三维最近点和时刻](../evidence/reviews/beforestep_r1/lux/original_b/physical_clearance.json) 与 [完整重放核验](../evidence/reviews/beforestep_r1/replay_validation.json) 可独立检查。

## 全部反事实：本批自检偏保守

按预注册逐一只信 B 第一眼被拒的 A1、B1、C2，不挑选，不补看，不重新调用 Lux3D。三次均到达、无碰撞，碰撞数 0/3。因此此次不能说“自检挡住了会撞的想象”；结论是本批自检偏保守。

| 只信的被拒 B | 实际终态 | 仿真总时长 | 证据 |
| --- | --- | --- | --- |
| B/A1 | 到达、无碰撞 | 104.0 s | [原始身份](../evidence/reviews/beforestep_r1/counterfactuals/A1/run_identity.json) |
| B/B1 | 到达、无碰撞 | 104.0 s | [原始身份](../evidence/reviews/beforestep_r1/counterfactuals/B1/run_identity.json) |
| B/C2 | 到达、无碰撞 | 119.16 s | [原始身份](../evidence/reviews/beforestep_r1/counterfactuals/C2/run_identity.json) |

## 迭代、训练与相关工作

V6/V7/V8 的源码、输入、生成资产、融合几何和失败结果保留。旧 gate_passage_001、终点 `(5.7,-0.5)` 的实验及训练控制移到附录：它们证明了工程闭环与网络运动，但对照同样能到达，没有证明 Lux3D 的必要性。固定 v4 实际训练 115490 行物理示教，部署权重与独立任务 15/16 评估均保留；新姿态网络、四眼实测和失败也保留，不继续训练迭代。

[训练附录](training.md) · [主动观察控制附录](observation-control.md) · [版本证据](milestones.md) · [旧 v0.3 报告](history/report_v03.md)。PSSNet、PVD、Robust Grasp Planning、Uncertain Regions 与 NBV-SC 为多候选形状、动作评价及补看提供研究依据；本项目贡献是受观测自检约束、同控制器完整预演与独立执行的轮腿导航实证，不主张全球首次或科学上只有 Lux3D 能实现。[相关工作](related-work.md)。

首页提供实际轨迹、全部候选与十二格预演的交互查看。当前是受控仿真实验，不是实机或月球部署。R1 新 Demo 由负责人使用完整保存数据制作；网页保留视频位置，现有 v0.3 视频明确作为历史，冻结发布不改。完整可运行源码、原资产、失败和恢复输入见 [仓库](../README.md)、[R1 数据说明](../evidence/reviews/beforestep_r1/README.md)。
