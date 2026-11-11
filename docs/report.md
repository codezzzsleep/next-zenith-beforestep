# 先见一步：看不见的那一面，先走一遍

Next Zenith · Aholo Lux3D。报告保留R1原窄道锚点与R2预注册场景组；R1主实验源码 `2147b2f`，R2源码身份逐场保存在原运行记录。完整结果见[R1执行记录](reviews/RESULT_BEFORESTEP_R1.md)与[R2执行记录](reviews/RESULT_BEFORESTEP_R2.md)。

锚点场景中，想象车是三台车里唯一安全到达的；12 个预注册场景中，决定性 8 个：到达 3、安全停车 3、碰撞 2（原因已查明）。


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


## 关卡：先选，再揭晓

每关先看真实第一眼，选策略，回放原物理轨迹，再看真值与全部候选、记分。[进入12关](../site/levels.html)。

<!-- SUITE-START -->
# 预注册月面场景组

场景组在任何本轮 Lux3D 结果之前冻结。选择只依据保守、see-dark、乐观和真实形状检验四次非 Lux 运行；各类别按种子从小到大取决定性与普通场景，stress_v8 直接使用已完成的 R1 锚点。冻结后不换场景、不放宽门槛、不迭代控制器。

原冻结 12 个场景，完成 12 个。未完成：无。

[冻结名单与预期](../config/suite/frozen.json) · [原始结果总表](../evidence/suite/summary.json)

## 候选池分布

| 类别 | 候选数 | 决定性 | 普通 | 无解 | 未归类 | 执行错误 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| F0 | 12 | 9 | 2 | 1 | 0 | 0 |
| F1 | 24 | 2 | 10 | 8 | 4 | 0 |
| F2 | 12 | 3 | 8 | 0 | 1 | 0 |
| F3 | 12 | 5 | 3 | 2 | 2 | 0 |

决定性：真实形状检验到达，乐观碰撞，保守停车或用满五眼。普通：真实形状与乐观均到达。无解：真实形状检验不到达。执行错误不会算成无解或被隐藏。此前错误池与参数调整理由保留在[决策记录](decisions.md)与[R2结果](reviews/RESULT_BEFORESTEP_R2.md)。

## 五次运行

| 场景 / 类别 / 分类 / 种子 | 保守 | see-dark | 乐观 | 真实形状检验 | 真实 Lux3D |
| --- | --- | --- | --- | --- | --- |
| stress_v8 / F0 / 决定性 / R1锚点 | 安全停车 · 5眼 · 142.2s · [身份](../evidence/reviews/beforestep_r1/section25_final_base/conservative/run_identity.json) | 到达 · 3眼 · 147.26s · [身份](../evidence/reviews/beforestep_r1/section25_final_base/see_dark/run_identity.json) | 碰撞 · 1眼 · 80.87s · [身份](../evidence/reviews/beforestep_r1/section25_final_base/optimistic/run_identity.json) | 到达 · 1眼 · 115.88s · [身份](../evidence/reviews/beforestep_r1/section25_final_base/truth/run_identity.json) | 到达 · 1眼 · 112.84s · [身份](../evidence/reviews/beforestep_r1/lux/original_b/run_identity.json) |
| suite_r2_v4_F0_001 / F0 / 决定性 / 1 | 安全停车 · 5眼 · 142.92s · [身份](../evidence/suite/scenes/suite_r2_v4_F0_001/runs/conservative/run_identity.json) | 到达 · 3眼 · 145.24s · [身份](../evidence/suite/scenes/suite_r2_v4_F0_001/runs/see_dark/run_identity.json) | 碰撞 · 1眼 · 80.83s · [身份](../evidence/suite/scenes/suite_r2_v4_F0_001/runs/optimistic/run_identity.json) | 到达 · 1眼 · 114.84s · [身份](../evidence/suite/scenes/suite_r2_v4_F0_001/runs/truth/run_identity.json) | 安全停车 · 2眼 · 54.58s · [身份](../evidence/suite/scenes/suite_r2_v4_F0_001/runs/imagination/run_identity.json) |
| suite_r2_v4_F0_005 / F0 / 普通 / 5 | 安全停车 · 5眼 · 143.98s · [身份](../evidence/suite/scenes/suite_r2_v4_F0_005/runs/conservative/run_identity.json) | 到达 · 3眼 · 151.76s · [身份](../evidence/suite/scenes/suite_r2_v4_F0_005/runs/see_dark/run_identity.json) | 到达 · 1眼 · 102.42s · [身份](../evidence/suite/scenes/suite_r2_v4_F0_005/runs/optimistic/run_identity.json) | 到达 · 1眼 · 114.6s · [身份](../evidence/suite/scenes/suite_r2_v4_F0_005/runs/truth/run_identity.json) | 安全停车 · 2眼 · 53.0s · [身份](../evidence/suite/scenes/suite_r2_v4_F0_005/runs/imagination/run_identity.json) |
| suite_r2_v4_F1_001 / F1 / 决定性 / 1 | 安全停车 · 5眼 · 111.74s · [身份](../evidence/suite/scenes/suite_r2_v4_F1_001/runs/conservative/run_identity.json) | 碰撞 · 4眼 · 91.03s · [身份](../evidence/suite/scenes/suite_r2_v4_F1_001/runs/see_dark/run_identity.json) | 碰撞 · 1眼 · 72.47s · [身份](../evidence/suite/scenes/suite_r2_v4_F1_001/runs/optimistic/run_identity.json) | 到达 · 2眼 · 124.38s · [身份](../evidence/suite/scenes/suite_r2_v4_F1_001/runs/truth/run_identity.json) | 安全停车 · 2眼 · 42.7s · [身份](../evidence/suite/scenes/suite_r2_v4_F1_001/runs/imagination/run_identity.json) |
| suite_r2_v4_F1_020 / F1 / 决定性 / 20 | 安全停车 · 5眼 · 129.12s · [身份](../evidence/suite/scenes/suite_r2_v4_F1_020/runs/conservative/run_identity.json) | 未完成 · 4眼 · 121.09s · [身份](../evidence/suite/scenes/suite_r2_v4_F1_020/runs/see_dark/run_identity.json) | 碰撞 · 1眼 · 79.24s · [身份](../evidence/suite/scenes/suite_r2_v4_F1_020/runs/optimistic/run_identity.json) | 到达 · 1眼 · 78.16s · [身份](../evidence/suite/scenes/suite_r2_v4_F1_020/runs/truth/run_identity.json) | 碰撞 · 1眼 · 61.46s · [身份](../evidence/suite/scenes/suite_r2_v4_F1_020/runs/imagination/run_identity.json) |
| suite_r2_v4_F1_003 / F1 / 普通 / 3 | 碰撞 · 4眼 · 134.49s · [身份](../evidence/suite/scenes/suite_r2_v4_F1_003/runs/conservative/run_identity.json) | 到达 · 5眼 · 129.45s · [身份](../evidence/suite/scenes/suite_r2_v4_F1_003/runs/see_dark/run_identity.json) | 到达 · 1眼 · 105.18s · [身份](../evidence/suite/scenes/suite_r2_v4_F1_003/runs/optimistic/run_identity.json) | 到达 · 1眼 · 99.64s · [身份](../evidence/suite/scenes/suite_r2_v4_F1_003/runs/truth/run_identity.json) | 到达 · 1眼 · 108.0s · [身份](../evidence/suite/scenes/suite_r2_v4_F1_003/runs/imagination/run_identity.json) |
| suite_r2_v4_F2_003 / F2 / 决定性 / 3 | 安全停车 · 5眼 · 83.06s · [身份](../evidence/suite/scenes/suite_r2_v4_F2_003/runs/conservative/run_identity.json) | 到达 · 4眼 · 165.2s · [身份](../evidence/suite/scenes/suite_r2_v4_F2_003/runs/see_dark/run_identity.json) | 碰撞 · 1眼 · 82.79s · [身份](../evidence/suite/scenes/suite_r2_v4_F2_003/runs/optimistic/run_identity.json) | 到达 · 1眼 · 124.92s · [身份](../evidence/suite/scenes/suite_r2_v4_F2_003/runs/truth/run_identity.json) | 安全停车 · 2眼 · 57.8s · [身份](../evidence/suite/scenes/suite_r2_v4_F2_003/runs/imagination/run_identity.json) |
| suite_r2_v4_F2_007 / F2 / 决定性 / 7 | 安全停车 · 5眼 · 83.33s · [身份](../evidence/suite/scenes/suite_r2_v4_F2_007/runs/conservative/run_identity.json) | 到达 · 4眼 · 157.28s · [身份](../evidence/suite/scenes/suite_r2_v4_F2_007/runs/see_dark/run_identity.json) | 碰撞 · 1眼 · 80.41s · [身份](../evidence/suite/scenes/suite_r2_v4_F2_007/runs/optimistic/run_identity.json) | 到达 · 1眼 · 112.56s · [身份](../evidence/suite/scenes/suite_r2_v4_F2_007/runs/truth/run_identity.json) | 到达 · 2眼 · 128.4s · [身份](../evidence/suite/scenes/suite_r2_v4_F2_007/runs/imagination/run_identity.json) |
| suite_r2_v4_F2_001 / F2 / 普通 / 1 | 安全停车 · 5眼 · 83.43s · [身份](../evidence/suite/scenes/suite_r2_v4_F2_001/runs/conservative/run_identity.json) | 到达 · 3眼 · 133.18s · [身份](../evidence/suite/scenes/suite_r2_v4_F2_001/runs/see_dark/run_identity.json) | 到达 · 1眼 · 102.5s · [身份](../evidence/suite/scenes/suite_r2_v4_F2_001/runs/optimistic/run_identity.json) | 到达 · 1眼 · 102.5s · [身份](../evidence/suite/scenes/suite_r2_v4_F2_001/runs/truth/run_identity.json) | 到达 · 1眼 · 102.7s · [身份](../evidence/suite/scenes/suite_r2_v4_F2_001/runs/imagination/run_identity.json) |
| suite_r2_v4_F3_002 / F3 / 决定性 / 2 | 安全停车 · 5眼 · 218.48s · [身份](../evidence/suite/scenes/suite_r2_v4_F3_002/runs/conservative/run_identity.json) | 到达 · 5眼 · 119.05s · [身份](../evidence/suite/scenes/suite_r2_v4_F3_002/runs/see_dark/run_identity.json) | 碰撞 · 1眼 · 80.4s · [身份](../evidence/suite/scenes/suite_r2_v4_F3_002/runs/optimistic/run_identity.json) | 到达 · 1眼 · 117.54s · [身份](../evidence/suite/scenes/suite_r2_v4_F3_002/runs/truth/run_identity.json) | 到达 · 1眼 · 107.6s · [身份](../evidence/suite/scenes/suite_r2_v4_F3_002/runs/imagination/run_identity.json) |
| suite_r2_v4_F3_004 / F3 / 决定性 / 4 | 安全停车 · 1眼 · 18.1s · [身份](../evidence/suite/scenes/suite_r2_v4_F3_004/runs/conservative/run_identity.json) | 未完成 · 4眼 · 129.63s · [身份](../evidence/suite/scenes/suite_r2_v4_F3_004/runs/see_dark/run_identity.json) | 碰撞 · 1眼 · 79.59s · [身份](../evidence/suite/scenes/suite_r2_v4_F3_004/runs/optimistic/run_identity.json) | 到达 · 1眼 · 106.44s · [身份](../evidence/suite/scenes/suite_r2_v4_F3_004/runs/truth/run_identity.json) | 碰撞 · 1眼 · 82.14s · [身份](../evidence/suite/scenes/suite_r2_v4_F3_004/runs/imagination/run_identity.json) |
| suite_r2_v4_F3_001 / F3 / 普通 / 1 | 未完成 · 2眼 · 111.83s · [身份](../evidence/suite/scenes/suite_r2_v4_F3_001/runs/conservative/run_identity.json) | 到达 · 3眼 · 125.97s · [身份](../evidence/suite/scenes/suite_r2_v4_F3_001/runs/see_dark/run_identity.json) | 到达 · 1眼 · 111.88s · [身份](../evidence/suite/scenes/suite_r2_v4_F3_001/runs/optimistic/run_identity.json) | 到达 · 1眼 · 107.64s · [身份](../evidence/suite/scenes/suite_r2_v4_F3_001/runs/truth/run_identity.json) | 到达 · 1眼 · 112.5s · [身份](../evidence/suite/scenes/suite_r2_v4_F3_001/runs/imagination/run_identity.json) |

B4在付费前发现并纠正预演中的旧右墙配置遗漏。上表全部新增场景的四基线随后统一重跑，与真实Lux使用相同源码；最初用于选取的四次结果仍保存在冻结名单中，没有据修正后的结果增删或替换场景。
[同源基线回归](../evidence/suite/pool/crater-target-baselines/manifest_results.json)。修正后分类发生变化的场景：无。

每项时间为原始 summary 的仿真总时长，包含该运行的接近与观察，不包含云端排队。自检计算与预演计算墙钟另在原运行中保留，不作为端到端速度优势。所有运行使用 rules，传感器、机器人与5cm规则保持冻结；真实Lux流程使用同一准入门槛、最多两眼，保守、see-dark与乐观对照保留最多五眼，真实形状检验也最多两眼。真实形状是独立检验，未提供给生产规划器。

## 候选与补看

| 场景 | 真实岩石 | 任务 / 成功 / 准入 | 原视角高度与方式 | 第二眼 | 6b |
| --- | --- | --- | --- | --- | --- |
| stress_v8 | A | 6 / 6 / 6 | look1/T1: 765px, native_ok=True, img | 否 | 否 |
| stress_v8 | B | 6 / 5 / 2 | look1/T2: 251px, native_ok=False, img | 否 | 否 |
| suite_r2_v4_F0_001 | A | 6 / 6 / 4 | look1/T1: 768px, native_ok=True, img | 是 | 否 |
| suite_r2_v4_F0_001 | B | 18 / 18 / 0 | look1/T2: 260px, native_ok=False, img; look2/T2: 527px, native_ok=True, img | 是 | 是 |
| suite_r2_v4_F0_005 | A | 9 / 9 / 0 | look1/T1: 805px, native_ok=True, img; look2/T1: 1249px, native_ok=True, imgs | 是 | 否 |
| suite_r2_v4_F0_005 | B | 12 / 12 / 1 | look1/T2: 248px, native_ok=False, img; look2/T2: 336px, native_ok=False, img | 是 | 否 |
| suite_r2_v4_F1_001 | A | 6 / 6 / 2 | look1/T1: 679px, native_ok=True, img | 是 | 否 |
| suite_r2_v4_F1_001 | B | 6 / 4 / 0 | look1/T2: 351px, native_ok=False, img | 是 | 否 |
| suite_r2_v4_F1_001 | C | 0 / 0 / 0 | 全程没有生成观测请求 | 是 | 否 |
| suite_r2_v4_F1_020 | A | 6 / 4 / 1 | look1/T1: 957px, native_ok=True, img | 否 | 否 |
| suite_r2_v4_F1_020 | B | 6 / 4 / 2 | look1/T2: 363px, native_ok=False, img | 否 | 否 |
| suite_r2_v4_F1_020 | C | 0 / 0 / 0 | 全程没有生成观测请求 | 否 | 否 |
| suite_r2_v4_F1_003 | A | 6 / 6 / 3 | look1/T1: 621px, native_ok=True, img | 否 | 否 |
| suite_r2_v4_F1_003 | B | 6 / 6 / 2 | look1/T2: 322px, native_ok=False, img，共享目标 B+C | 否 | 否 |
| suite_r2_v4_F1_003 | C | 6 / 6 / 2 | look1/T2: 322px, native_ok=False, img，共享目标 B+C | 否 | 否 |
| suite_r2_v4_F2_003 | A | 9 / 8 / 5 | look1/T1: 721px, native_ok=True, img; look2/T1: 1715px, native_ok=True, imgs | 是 | 否 |
| suite_r2_v4_F2_003 | B | 18 / 18 / 4 | look1/T2: 223px, native_ok=False, img; look2/T2: 773px, native_ok=True, img | 是 | 是 |
| suite_r2_v4_F2_007 | A | 6 / 6 / 5 | look1/T1: 705px, native_ok=True, img | 是 | 否 |
| suite_r2_v4_F2_007 | B | 12 / 10 / 2 | look1/T2: 269px, native_ok=False, img; look2/T2: 509px, native_ok=False, img | 是 | 否 |
| suite_r2_v4_F2_001 | A | 6 / 6 / 2 | look1/T1: 728px, native_ok=True, img | 否 | 否 |
| suite_r2_v4_F2_001 | B | 6 / 6 / 6 | look1/T2: 248px, native_ok=False, img | 否 | 否 |
| suite_r2_v4_F3_002 | A | 6 / 4 / 4 | look1/T1: 800px, native_ok=True, img | 否 | 否 |
| suite_r2_v4_F3_002 | B | 6 / 6 / 1 | look1/T2: 243px, native_ok=False, img | 否 | 否 |
| suite_r2_v4_F3_004 | A | 6 / 6 / 6 | look1/T1: 754px, native_ok=True, img | 否 | 否 |
| suite_r2_v4_F3_004 | B | 6 / 6 / 2 | look1/T2: 257px, native_ok=False, img | 否 | 否 |
| suite_r2_v4_F3_004 | C | 0 / 0 / 0 | 全程没有生成观测请求 | 否 | 否 |
| suite_r2_v4_F3_001 | A | 6 / 4 / 4 | look1/T1: 772px, native_ok=True, img | 否 | 否 |
| suite_r2_v4_F3_001 | B | 0 / 0 / 0 | 全程没有生成观测请求 | 否 | 否 |

从未形成观测请求的目标也以零任务保留；若一个连通观测目标对应多块真实岩石，各岩石行共享同一批任务身份，不能相加当作额外独立生成。每份成功、失败与被拒候选均保留；第二眼单图首次零准入时只追加同字节 6b 一批，仍零准入就停止。两眼都 native_ok 的两图分支按原协议三份执行。

## 赛后真值与全部拒绝反事实

| 场景 | 3D最小间隙mm | XY包络间隙mm | 乐观原路线压入mm | 反事实碰撞 / 完成试验 | 反事实终态分布 | 不能执行的拒绝候选 |
| --- | ---: | ---: | ---: | --- | --- | ---: |
| stress_v8 | 47.541 | 0.000 | 218.989 | 0 / 3 | 到达3 | 0 |
| suite_r2_v4_F0_001 | 416.194 | 196.984 | 212.560 | 4 / 20 | 安全停车2、碰撞4、到达14 | 0 |
| suite_r2_v4_F0_005 | 970.602 | 839.352 | 29.071 | 0 / 20 | 安全停车17、到达3 | 0 |
| suite_r2_v4_F1_001 | 344.242 | 187.223 | 190.572 | 4 / 8 | 安全停车4、碰撞4 | 0 |
| suite_r2_v4_F1_020 | 0.710 | 0.000 | 330.000 | 5 / 5 | 碰撞5 | 0 |
| suite_r2_v4_F1_003 | 155.317 | 36.886 | 0.000 | 0 / 7 | 到达7 | 0 |
| suite_r2_v4_F2_003 | 405.283 | 178.033 | 143.253 | 0 / 17 | 安全停车17 | 0 |
| suite_r2_v4_F2_007 | 181.992 | 71.292 | 168.460 | 0 / 9 | 安全停车1、到达8 | 0 |
| suite_r2_v4_F2_001 | 193.733 | 81.055 | 0.000 | 0 / 4 | 到达4 | 0 |
| suite_r2_v4_F3_002 | 107.740 | 0.000 | 231.371 | 0 / 5 | 到达5 | 0 |
| suite_r2_v4_F3_004 | 0.939 | 0.000 | 265.028 | 4 / 4 | 碰撞4 | 0 |
| suite_r2_v4_F3_001 | 148.585 | 36.125 | 0.000 | 0 / 0 | 无 | 0 |

3D量来自每个保存姿态的原 MuJoCo 可碰撞几何；XY矩形与真实扫描平面包络是单独的复盘近似。二者同时报告，XY相交不等于真实3D接触。碰撞按原始接触记录优先判断，离散保存姿态的正间隙不能抵消接触事件。反事实枚举每一眼每份被拒候选，不挑选；第二眼候选在原第一眼与移动前缀重放之后干预，不在第一眼泄露未来观测。完成试验包括因无路线而停车，不等于完成通行，所以终态分布同时报告。不能形成可执行反事实的失败另列，不能当作“不会撞”。

## 预先约定的结论

**想象策略实际发生碰撞：suite_r2_v4_F1_020、suite_r2_v4_F3_004。这是最重要的安全边界，首页与总表同时公开。**
决定性完成 8 个：想象到达 3，安全终止 3，碰撞 2。
没有满足“决定性场景到达至少2/3且无碰撞”的预注册条件，结论限于逐项实测的有效范围。
普通场景完成 4、想象到达 3；相对乐观额外眼数与仿真时间分别为 [1, 0, 0, 0]、[-49.42, 2.82, 0.2, 0.62]s。
未到达运行的较短仿真时间可能来自提前停车；这里比较终态时长，不能解释成更快完成任务。
被拒候选反事实碰撞 17/102，另 0 份不能执行。自检拒绝的候选中出现过会碰撞的想象，比例和场景逐项公开。
第二眼真实触发：suite_r2_v4_F0_001、suite_r2_v4_F0_005、suite_r2_v4_F1_001、suite_r2_v4_F2_003、suite_r2_v4_F2_007；6b：suite_r2_v4_F0_001、suite_r2_v4_F2_003。
真实第二眼共 5 次：到达 1、安全终止 4、碰撞 0。

### 按类别的实测范围

| 类别 | 决定性到达 / 安全终止 / 碰撞 | 普通到达 / 总数 |
| --- | --- | --- |
| F0 | 1 / 1 / 0 | 0 / 1 |
| F1 | 0 / 1 / 1 | 1 / 1 |
| F2 | 1 / 1 / 0 | 1 / 1 |
| F3 | 1 / 0 / 1 | 1 / 1 |

## 未到达与碰撞的原因

| 场景 / 类别 | 原始判断 | 事件或物理接触 |
| --- | --- | --- |
| suite_r2_v4_F0_001 / F0 | 追加后仍零准入 | {"kind": "sampling_stop", "look": 2, "target": "T2", "total_samples": 12, "generated_candidates": 12, "admitted": 0, "action": "safe_stop_then_review_section_2_4"} |
| suite_r2_v4_F0_005 / F0 | 没有可执行准入路线 | {"kind": "plan", "policy": "imagination", "look": 2, "path": null, "reason": "imagined_blocked", "margin_vs_truth": null} |
| suite_r2_v4_F1_001 / F1 | 没有可执行准入路线 | {"kind": "plan", "policy": "imagination", "look": 2, "path": null, "reason": "imagined_blocked", "margin_vs_truth": null} |
| suite_r2_v4_F1_020 / F1 | 真实物理接触 | {"body": "obstacle2", "robot_geom": null, "pos": [7.405, -0.656, 0.089], "t": 61.458}；未形成生成请求的岩石：C。候选自检和预演只覆盖实际形成的候选，不能证明未观测岩石安全。 |
| suite_r2_v4_F2_003 / F2 | 追加后仍零准入 | {"kind": "sampling_stop", "look": 2, "target": "T2", "total_samples": 12, "generated_candidates": 12, "admitted": 0, "action": "safe_stop_then_review_section_2_4"} |
| suite_r2_v4_F3_004 / F3 | 真实物理接触 | {"body": "obstacle1", "robot_geom": null, "pos": [6.681, -0.3, 0.1], "t": 82.14}；未形成生成请求的岩石：C。候选自检和预演只覆盖实际形成的候选，不能证明未观测岩石安全。；实际碰撞位置在真值B占地内，却不在两份准入B候选的占地内；候选只约覆盖真值B投影的14%。12格预演没有覆盖这个真实接触位置。 [原始比较](../evidence/suite/actual-collisions/suite_r2_v4_F3_004/diagnostic.json) |

这是有限扫描岩石、有限摆放和极区低太阳角下的受控仿真实验，不支持“对任何场景都有效”或“通用”的结论。每个数字均能追溯到原始运行身份、任务与保全清单。
<!-- SUITE-END -->

<!-- R3-FAILURE-START -->
## 失败分析：想象只能检验看得见的一面

### F1_020：从没被看见的石头

C 完全藏在 A 后面，没有形成观测目标，任务数为 0；原计划路线侵入 C 的真实占地。原想象占据规则是乐观占据加候选占地，视线遮挡 HIDDEN 与未观测 UNSEEN 只要不落在候选中就可通行。**这是方法设计的缺陷，不是 Lux3D 没有生成 C 的问题。**

### F3_004：背面想错，正面仍通过自检

| 场景 | A | B | 地形 | 太阳高度 / 方位 |
| --- | --- | --- | --- | --- |
| stress_v8 | rock_07，0.55 m，(4.55, -0.73)，90° | moon_rock_04，0.42 m，(6.86, 0.22)，-26° | 窄道 | 10.0° / 35.0° |
| F3_004 | rock_07，0.53 m，(4.51, -0.70)，92° | moon_rock_04，0.43 m，(6.76, 0.16)，-23° | 开阔月面 + 1 个坑 | 10.4° / 38.8° |

B 的 A1、A2 轮廓 IoU 分别为 0.8429、0.8588，通过冻结自检；原计划路线却按真值压入 B 26.5 cm，实际发生碰撞。自检只约束可见的一面，不能证明不可见背面的假设正确。

锚点的三维最小间隙 **47.541 mm** 与二维包络间隙 **0 mm** 必须一起理解：同一块扁平石板、几乎相同的摆放换到开阔地形就撞了。**锚点的成功不稳健。** R1 原锚点仍是一眼到达的预注册结果，视频继续使用它，不替换成赛后修订结果。

### 全部准入候选的背面误差

![原R1和R2全部准入候选的赛后背面误差分布](../site/media/r3-back-error.png)

原 R1 + R2 共 **64** 份通过自检的候选，其中 **23** 份的背面比关联真值短 **5 cm 以上**。误差为每次观测时沿机器人前进轴的候选占地最远端减真值最远端；图中的负 **5 cm** 线是冻结余量。联合观测对关联真值并集统计，所有准入候选逐份入列，真值仅用于赛后诊断，不能证明阴影中的几何已经还原。

[原始统计与每份候选身份](../evidence/reviews/beforestep_r3/back-error/stats.json) · [两次失败的原始数值](../evidence/reviews/beforestep_r3/failure-facts.json) · [给负责人渲染视频的数据索引](../evidence/video/index.json)

<!-- R3-FAILURE-END -->

## 沙盒

[自由摆石头](../site/sandbox.html)是轻量几何规划，不实时调用Lux3D或执行物理仿真。原12场首眼几何8/12一致，全部不一致公开。

## 迭代、训练与相关工作

V6/V7/V8 的源码、输入、生成资产、融合几何和失败结果保留。旧 gate_passage_001、终点 `(5.7,-0.5)` 的实验及训练控制移到附录：它们证明了工程闭环与网络运动，但对照同样能到达，没有证明 Lux3D 的必要性。固定 v4 实际训练 115490 行物理示教，部署权重与独立任务 15/16 评估均保留；新姿态网络、四眼实测和失败也保留，不继续训练迭代。

[训练附录](training.md) · [主动观察控制附录](observation-control.md) · [版本证据](milestones.md) · [旧 v0.3 报告](history/report_v03.md)。PSSNet、PVD、Robust Grasp Planning、Uncertain Regions 与 NBV-SC 为多候选形状、动作评价及补看提供研究依据；本项目贡献是受观测自检约束、同控制器完整预演与独立执行的轮腿导航实证，不主张全球首次或科学上只有 Lux3D 能实现。[相关工作](related-work.md)。

首页提供实际轨迹、全部候选与十二格预演的交互查看。当前是受控仿真实验，不是实机或月球部署。R1 新 Demo 由负责人使用完整保存数据制作；网页保留视频位置，现有 v0.3 视频明确作为历史，冻结发布不改。完整可运行源码、原资产、失败和恢复输入见 [仓库](../README.md)、[R1 数据说明](../evidence/reviews/beforestep_r1/README.md)。
