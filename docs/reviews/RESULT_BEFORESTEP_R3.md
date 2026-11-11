# RESULT_BEFORESTEP_R3

执行规格：[SPEC_BEFORESTEP_R3.md](SPEC_BEFORESTEP_R3.md)。R1/R2预注册结果仍为主结果；全部新增方法和实验标为赛后修订。

| 小项 | 内容 | 状态 | 提交/证据 |
| --- | --- | --- | --- |
| P0.1 | 首页/报告顺序与失败分析 | 完成 | c4b18f3；Pages e08f20d/public browser0 |
| P0.2 | 全部准入候选背面误差统计/数字核验 | 完成 | c4b18f3；Pages e08f20d/public browser0 |
| V0 | 指定原运行的全部公开视频数据索引 | 完成 | c4b18f3；Pages e08f20d/public browser0 |
| P0.3 | 本地/公网验收与PDF/Pages | 完成 | c4b18f3；Pages e08f20d/public browser0 |
| S1 | imagination_strict与预测阴影 | 完成 | 4d53214；80单测pass；原pipeline.py原样 |
| S2 | 单测/太阳诊断/全部R1回归/两个替身 | 完成 | v3五R1pass/四standin all_passed=true |
| E1 | 原12冻结场景赛后修订复测 | 进行中 | 正式v3全12；首眼复用，新增任务≤170 |
| E2 | 指定留出场景六栏运行 | 未开始 | — |
| V1 | 加入三个修订想象视频记录 | 未开始 | — |
| D | 修订结果/对照/报告/相关工作/最终验收发布 | 未开始 | — |

## 身份、预算与保护

起点main dae2b58；R3原件SHA815fb6b7a92a9c0e2c59eb87e4ac49ee295c2110375b9b07201a3a0e98bfaa59。R1/R2原结果、evidence、freeze不改；R2已有168真实任务全部终态。本轮新增上限170，累计最多338/360，第一眼同字节复用，不重create。

R3显式新增策略imagination_strict最多5眼，原imagination仍最多2眼、原分支不改。所有冻结阈值、机器人、相机/传感器、rules、3.17.0依赖保持；不训练、不渲染Demo。源变动后先单测/五R1回归、太阳方向诊断与两个standin通过才paid。

P0只使用既有真实数据。背面统计预先定义：以每次实际观测目标state.local_frame.yaw0对应机器人的前进轴，将准入占地与该目标关联真值占地投影；最远端差=候选−真值，负值表示背面更短。联合观测目标对关联真值并集统计，全部准入都入列、不挑。5cm余量线为−0.05m，统计严格短于该线的数量；这是赛后真值诊断，不输入planner。

视频索引每文件指向公开repo实际可取的原字节或gzip存储对象并注明解压/原SHA，渲染资产指向assets命名空间。不仅给外部tar，原包继续保留。新对象可以复用已公开内容SHA，原R1/R2文件不修改。

## P0 与视频索引本地完成

背面误差脚本实际读全部原准入64份（R1 8/R2 56），23份短于真值5cm以上，原source/footprint/decision SHA和task身份每份保留于back-error/stats.json；图只用于赛后分析。R3首页顺序已改为摘要→两影子→锚点八点→关卡→结果摘要/两collision原因/可展开原详表→失败章/统计图→sandbox/附录。原R2完整表原文字节保留。F3 B IoU0.8429/0.8588、路线压入26.5cm、锚点47.541mm/二维0一起写，并明说不稳健；F1 C任务0、路线侵入C、方法设计错误不是Lux的问题。

`check_r1_browser --name r3-P0-local-corrected --pdf` exit0/9回放11GLB12预演3历史20learning/390/0pageHTTP，第一版新图表无自适应导致overflow日志保留，已comparison/table-wrap修正；源src完全未改。数字audit exit0/原R1R2数字+64/23/26.5及新场景表，20docs303links全0。PDF14页1775024bytes/SHA3b8e6c1ed56601a1154cc4cd39818276978987f02714395dfc0b5ffd39388b3e，实际读取所有新关键文字；旧R2 Md/HTML/PDF原字节归档pre-revision。

V0指定19run（锚点9+两失败场各5）/1193独立公开byte对象全部本地SHA验证，含RGB/depth/dark/state/zmax、原轨迹/事件/场景/summary、全部75候选记录的world OBJ/自检指标、每预演轨迹及eval/physical、岩石/纹理/height/robot assets。缺失原postmortem只在新sidecar复算原每qpos，无推进sim或改原结果；vendor alias字节公开在assets对象不靠旧目录取文件。索引逐条path/encoding/sourceSHA可从repo/LFS取，gzip注明解压恢复原字节，不需要仓库外tar。还需实际push/LFS远端检验/P0 Pages公网验收。当前R3新增paid0/170、原168全部不重create。

P0公网已实际完成：Pages e08f20d393e1e49a0dd7b840677c1ddc55c4f552 built/error null，r3-P0-public browser exit0/9回放11GLB12预演3历史20learning/全部图和视频索引链接/390/0pageHTTP，PDF源SHA同本地。原R1/R2 protected tracked文件与dae2b58 diff空。接续§3；没有新增paid。

## S1 实现与 S2 当前检查

新策略放在独立 `src/beforestep/strict_pipeline.py`，原 `pipeline.py` 与 cfffaf8 原件逐字节相同；`navigation/map.py` 只新增 strict 分支，原 imagination 占据在 R1 地图逐格相同。严格方法最多五眼，只有预测阴影解释的 DARK 可以通行，HIDDEN/UNSEEN 保守。阴影采用固定 5cm 栅格、0.05–5.00m 光线，由同一个 `scene.sun_dir()` 取得指向太阳的反向；高度取已知物理高度场、观测 zmax、准入世界网格的逐格最大值。没有新增可调门槛。

`python3 -m unittest discover -s tests -v` 已实际通过74项（3.083s），含方块阴影长度/方向、三角形格内最高点、strict未知占据、原R1想象逐格回归及170预算/uncertain/旧身份不重建。日志 `outputs/qa/r3/S2/unit-tests-with-budget.log`。全五R1回归已启动于 `outputs/qa/r3/S2/R1-regression`；四基线已通过，完整真实重放仍在执行，未在它通过之前做新实验或付费。

太阳诊断 [diagnostic.json](../../evidence/reviews/beforestep_r3/sun-diagnostic/diagnostic.json)、[差异图](../../evidence/reviews/beforestep_r3/sun-diagnostic/difference.png) 保留原全图 IoU0.0931619401、可观测非禁行地面域0.1489637306，反向0.0504351266。方向已按渲染函数与方块单测核对。低IoU的进一步只读诊断：该地面域424个DARK格里，416个像素命中比投影地面更近的表面（沿用原HIDDEN的0.10m深度条件）；原地图投影z=0地面，而DARK不像HIDDEN做遮挡判别，会把前景暗岩面赋给后方地面格。亮度DARK也并非纯几何阴影。深度一致地面域IoU0.04同样保留，不调参数去拟合，也不改相机/传感器/地图。真值只进入诊断和明确的truth替身。

替身预期在运行前登记：`stress_v8 --policy imagination_strict --imagine truth` 应到达；`suite_r2_v4_F1_020` 同命令应不会撞C。还用相同两场的离线扫描候选走生产注册、自检、所有预演和独立执行，明确标为替身、0付费。全部回归完成后才启动。

真实运行器 `ops/run_r3_chain.py` 只复制/复用首眼，后面几眼用新策略实际位置的观测，不复用旧方法不同位置的第二眼。首眼五文件SHA与目标输入一致性必须通过；不一致退出并调查，绝不新建首眼任务。`ops/r3_lux_budget.py` 在创建前锁定身份，新增170硬上限，旧R1/R2身份快照不计为新增、且记录丢失时拒绝重建。known/uncertain只查询，预算包含reserved/uncertain。

## E1/E2 运行前预期与固定次序

完整逐场预期、配置SHA与指定留出次序在 [experiment-plan.json](../../evidence/reviews/beforestep_r3/experiment-plan.json)，在真实运行前提交并push。E1是看过原结果后的已知场景复测，永远不计样本外证据。全部场景预期完整无碰撞到达、≤5眼，所有选定候选世界的预演均完成且无碰撞；零准入严格按12份规则停车，实际好坏逐项对照，不事后调参数。

| 场景 | 特定预期 |
| --- | --- |
| stress_v8 | 锚点应到达 |
| suite_r2_v4_F0_001 | 完整安全到达 |
| suite_r2_v4_F0_005 | 完整安全到达 |
| suite_r2_v4_F1_001 | 完整安全到达 |
| suite_r2_v4_F1_020 | 避免未见C的碰撞 |
| suite_r2_v4_F1_003 | 完整安全到达 |
| suite_r2_v4_F2_003 | 完整安全到达 |
| suite_r2_v4_F2_007 | 完整安全到达 |
| suite_r2_v4_F2_001 | 完整安全到达 |
| suite_r2_v4_F3_002 | 完整安全到达 |
| suite_r2_v4_F3_004 | 避免B背面偏短导致的碰撞 |
| suite_r2_v4_F3_001 | 完整安全到达 |

E2固定次序F0_002、F2_011、F3_005，预算剩余再F0_003、F3_006；F1无未使用的决定性场景。每场在当前源码跑四基线和原/修订想象，共用首眼任务，不根据基线再选或跳场。本轮先E1再E2，新增170/累计最多338，不超过原360。

S2完整R1 gate实际终态pass：stuck/arrived/collision/arrived，真实重放arrived·1眼·112.84s；全部t/qpos/phase/control_actions/control_sources逐项相同，NPZ SHA仍6b1481752708b9a2c9039ad91e55f98493714924afdd52da1be0baaee4758d1e。原件 [regression.json](../../evidence/reviews/beforestep_r3/regression/regression.json)，74单测日志同目录。现在四个truth/生产注册替身实际启动，尚无新增paid。

### S2 v1 失败与选点排查（0新增任务）

锚点truth替身实际stuck·4眼·116.68s，无碰撞；锚点生产注册替身实际stuck·4眼·112.54s，无碰撞。F1_020 truth替身stuck·1眼·18.1s，没有撞C；其生产注册替身已stuck·2眼·48.84s、无碰撞。所有原输出保留于 `outputs/qa/r3/S2/standins/`，未把失败写通过，付费门卫关闭。

[保存地图选点诊断](../../evidence/reviews/beforestep_r3/viewpoint-diagnostic/diagnostic.json) 发现新strict代码额外按strict占据过滤了unknown，改变R3要求沿用的保守选点排序。F1_020首眼原规则前40有可达(1.892,−0.8)，过滤后没有；锚点第4眼原规则最高135格且(3.871,0.6)可达，过滤后最高13格，低于原20格条件，于是提前no_viewpoint。修复仅恢复保守观察需求掩码，不改原选点函数、控制器、传感器、5cm或冻结参数；等已有离线作业终态，再改src并重新过全部单测、全五R1gate、两场替身。v1全部失败保留。

S2 v1四次替身全部终态，[v1原始summary](../../evidence/reviews/beforestep_r3/standins/v1/summary.json) 保留；E1门卫因all_passed=false退出1，未创建任何付费任务。新strict已恢复保守观察需求，75项单测实际pass/10.692s；完整v2回归 `outputs/qa/r3/S2-v2/R1-regression` 正在运行，仍核原R1所有数组，太阳实现/固定参数不变。v2替身只复用逐字节相同的旧离线首眼扫描资产，后面几眼重新实际观测，独立输出目标为 `evidence/reviews/beforestep_r3/standins/v2/summary.json`，当前尚未完成，不宣称通过。

## S2 v2：源回归通过，锚点到达预期未满足

[全五R1回归](../../evidence/reviews/beforestep_r3/regression/v2/regression.json) 已实际pass，75项单测、12个预演全无碰撞，真实重放五个数组与原R1完全相同。原扫描与物理碰撞网格的预测阴影逐格相同（IoU1.0），方向/坐标未发现错误；不调参数拟合DARK。

[四个v2替身原记录](../../evidence/reviews/beforestep_r3/standins/v2/summary.json)：锚点truth5眼142.2s停车、生产注册5眼135.42s停车；F1_020 truth5眼129.12s停车、生产注册2眼48.84s停车，全无碰撞。锚点真值替身的5个轨迹数组与保守车完全相同；[保存地图诊断](../../evidence/reviews/beforestep_r3/standins/v2/blockage-diagnostic.json) 显示只放开某一类未知仍无路，原全部未知放开的想象可以规划。规定的锚点到达预期未满足，保持all_passed=false，不把停车冒充通过，不创建新增任务。

为了完成不依赖新增付费的工作，按已提交12名单用真实旧首眼资产运行新策略；只mode=reuse、不会加载key/调用provider，需要新样本就保留实际观测与请求等待，不改变门槛/输入/名单。新source原R1回归已过，先复用再判断尚未完成项；这些是已知场景赛后修订复测，不是样本外证据。

云端实际只读查询旧R2任务6376018成功/status3/1.787s：[安全摘要](../../evidence/reviews/beforestep_r3/cloud-query.json)。未创建、上传或新生成。当前问题是严格方法的锚点验收。

8份替身与复盘完整保全：[stress清单](../../evidence/reviews/beforestep_r3/checks/stress_v8/manifest.json)、[F1_020清单](../../evidence/reviews/beforestep_r3/checks/suite_r2_v4_F1_020/manifest.json)。完整外包分别499050306与300576788bytes，路径/SHA在manifest；公开对象87.172MB/30.934MB，每scene低于150MB，422对象实际解压SHA/字节全通过。大native/RGBD原件在完整外包，P0视频指定19个原运行1193对象仍全部公开repo/LFS，不以外包替代视频索引。归档manifest的st_size属性调用错误已修，已完成tar原件复用核对member名字/size、不重包；初始失败log保留。

### v2 stress_v8-truth summary 原文

```json
{
  "policy": "imagination_strict",
  "tag": "imagination_strict",
  "see_dark": false,
  "imagine": "truth",
  "result": "stuck",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "stress_v8",
  "goal": [
    10.5,
    0.0
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 141.0,
  "sensor_mode": "live",
  "looks": 5,
  "final_pose": [
    4.033,
    0.382,
    -7.39
  ],
  "sim_time_s": 142.2,
  "wall_s": 77.2,
  "collision": null
}
```

### v2 suite_r2_v4_F1_020-truth summary 原文

```json
{
  "policy": "imagination_strict",
  "tag": "imagination_strict",
  "see_dark": false,
  "imagine": "truth",
  "result": "stuck",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F1_020",
  "goal": [
    10.000132,
    -0.030448
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 127.92,
  "sensor_mode": "live",
  "looks": 5,
  "final_pose": [
    1.668,
    -0.789,
    4.69
  ],
  "sim_time_s": 129.12,
  "wall_s": 80.1,
  "collision": null
}
```

### v2 stress_v8-registered summary 原文

```json
{
  "policy": "imagination_strict",
  "tag": "imagination_strict",
  "see_dark": false,
  "imagine": "lux",
  "result": "stuck",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "stress_v8",
  "goal": [
    10.5,
    0.0
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 134.22,
  "sensor_mode": "live",
  "looks": 5,
  "final_pose": [
    3.975,
    0.38,
    -8.07
  ],
  "sim_time_s": 135.42,
  "wall_s": 228.1,
  "collision": null
}
```

### v2 suite_r2_v4_F1_020-registered summary 原文

```json
{
  "policy": "imagination_strict",
  "tag": "imagination_strict",
  "see_dark": false,
  "imagine": "lux",
  "result": "stuck",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F1_020",
  "goal": [
    10.000132,
    -0.030448
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 47.64,
  "sensor_mode": "live",
  "looks": 2,
  "final_pose": [
    2.283,
    0.184,
    7.16
  ],
  "sim_time_s": 48.84,
  "wall_s": 149.6,
  "collision": null
}
```

### v3 整合修复：补看也使用当前策略的可通行定义

[只读保存地图诊断](../../evidence/reviews/beforestep_r3/standins/v2/view_motion_policy_diagnostic.json) 明确：固定Rturn0.57、相同N.choose排序，第3眼严格占据可达(5.445,−0.4)，旧保守占据没有可达候选；第4眼严格占据可达(6.064,−0.6)，旧保守也没有。v2只给目标路线应用了严格占据，却给补看路线/转向圈继续硬套旧保守占据，违反新策略已解释DARK可通行的统一定义；这是整合遗漏，不改冻结规则去拟合到达。

修复只在新strict模块：补看选点/路径也用同一严格占据，HIDDEN/UNSEEN仍阻塞，所有采纳世界先完整预演路径与最终相机转向，全部通过才移动；无模型时保持既有已见空间重试。N.choose算法、Rturn、512px、5cm、控制/机器人/相机/太阳均未改；H加入出发前已观测ob0.zmax，满足全部地图可见高度逐格max。79项单测实际pass/11.343s，含原consv排序与模型解释Solar圈后前向观察点可达；新的五R1 gate/四个truth与生产注册替身运行于 `outputs/qa/r3/S2-v3`。v1/v2失败all_passed=false与原输出保持，不改验收预期。

v2的旧12复用波次8终态（7停车、1碰撞）/4待样本，原路径`outputs/r3/frozen`不写；F1_003碰撞134.486s/obstacle2显著记录，source与原consv对照待复盘。新版必须全部12在独立v3目录重跑，保留旧版，当前0新增paid。

已知SDK身份可以跨相同字节的文件路径复用：当前inputs重绑定但保留original_task_inputs，验证imageSHA/identity/双图字段/GLB SHA，不改旧ledger；只在全state（除路径）/pose/time/所有obs字节和旧cache代码身份相同时复用旧元数据与自检，不伪造cacheID。未知/uncertain仍等待，不重建。

v3完整五R1回归实际通过，[原记录](../../evidence/reviews/beforestep_r3/regression/v3/regression.json)；79单测、真实重放全部5数组/NPZ SHA仍同原。新strict truth锚点已到达·5眼·232.52s·0碰撞，完成指定预期，源整合修复有效；F1及生产注册替身尚在运行，先等其终态，不提前新增任务。

## S2 v3 完成，进入正式E1

[四个完整替身](../../evidence/reviews/beforestep_r3/standins/v3/summary.json) 已全部终态、all_passed=true：锚点truth到达5眼232.52s、生产注册到达5眼228.02s；F1_020 truth到达4眼155.51s、生产注册2眼48.84s安全停车，均未碰撞。完整peek路径与最后朝向全部先在对应模型世界预演；保持S2明确预期不改。当前80项单测11.091s实际pass（多出的截止时间case验证已过11/14禁止create、旧任务仍可恢复），五R1源回归/原全部数组/SHA通过，实际源4d53214。

正式v3 E1独立目录`outputs/r3/v3/frozen`，全部原12名单按既定次序，各一次strict真实Lux；第一眼只用已通过原数组核对的R1缓存/原R2真实数据。已知同字节后续任务只在SDK身份和输入SHA完全相同才复用，旧ledger不写；新视角产生的新任务在R3budget创建前落ledger≤170。原v2 8终态/4待样本保留不覆写；本次修复后整个12重跑，不只重跑失败例。日期11/11，未到11/14关口，不收缩名单/预算。

### v3 stress_v8-truth summary 原文

```json
{
  "policy": "imagination_strict",
  "tag": "imagination_strict",
  "see_dark": false,
  "imagine": "truth",
  "result": "arrived",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "stress_v8",
  "goal": [
    10.5,
    0.0
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 231.32,
  "sensor_mode": "live",
  "looks": 5,
  "final_pose": [
    10.492,
    -0.002,
    18.36
  ],
  "sim_time_s": 232.52,
  "wall_s": 133.9,
  "collision": null
}
```

### v3 suite_r2_v4_F1_020-truth summary 原文

```json
{
  "policy": "imagination_strict",
  "tag": "imagination_strict",
  "see_dark": false,
  "imagine": "truth",
  "result": "arrived",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F1_020",
  "goal": [
    10.000132,
    -0.030448
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 154.31,
  "sensor_mode": "live",
  "looks": 4,
  "final_pose": [
    9.993,
    -0.035,
    15.63
  ],
  "sim_time_s": 155.51,
  "wall_s": 92.1,
  "collision": null
}
```

### v3 stress_v8-registered summary 原文

```json
{
  "policy": "imagination_strict",
  "tag": "imagination_strict",
  "see_dark": false,
  "imagine": "lux",
  "result": "arrived",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "stress_v8",
  "goal": [
    10.5,
    0.0
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 226.82,
  "sensor_mode": "live",
  "looks": 5,
  "final_pose": [
    10.491,
    -0.0,
    23.35
  ],
  "sim_time_s": 228.02,
  "wall_s": 289.6,
  "collision": null
}
```

### v3 suite_r2_v4_F1_020-registered summary 原文

```json
{
  "policy": "imagination_strict",
  "tag": "imagination_strict",
  "see_dark": false,
  "imagine": "lux",
  "result": "stuck",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F1_020",
  "goal": [
    10.000132,
    -0.030448
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 47.64,
  "sensor_mode": "live",
  "looks": 2,
  "final_pose": [
    2.283,
    0.184,
    7.16
  ],
  "sim_time_s": 48.84,
  "wall_s": 150.0,
  "collision": null
}
```
