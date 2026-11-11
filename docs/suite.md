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
普通场景完成 4、想象到达 3；相对乐观额外眼数与仿真时间分别为 [1, 0, 0, 0]、[-49.42, 2.819999999999993, 0.20000000000000284, 0.6200000000000045]s。
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
