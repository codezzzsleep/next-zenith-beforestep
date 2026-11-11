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
| E1 | 原12冻结场景赛后修订复测 | 完成 | f971519数据；12原summary/17CF/全复盘/完整tar+publicmanifest/独立远端下载通过，frozen-complete.json阶段证明 |
| E2 | 指定留出场景六栏运行 | 进行中 | E1 proof454951a已远端确认；F0_002六栏已完成；F2_011同身份中断恢复配准，固定其余场继续 |
| V1 | 加入三个修订想象视频记录 | 完成 | b00edc0已push；22run/1544byte本地pass；306LFS/407763387bytes从origin独立下载SHA/size全部pass |
| D | 修订结果/对照/报告/相关工作/最终验收发布 | 进行中 | 恢复与V1改动后85单测pass；最终统计/页面/PDF/公网待E2终态 |

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

## 正式实验终态与后处理

正式E1使用冻结源码4d53214，原80单测与五R1门卫已通过；新会话全82单测实际通过（24.938s/exit0），含两个prefix边界反例。[单测原日志](../../evidence/reviews/beforestep_r3/final-verification/unit-tests.log)。[当前原字节核对](../../evidence/reviews/beforestep_r3/final-verification/integrity.json) 实核3995个受保护R1/R2文件无变化、54份源码与正式身份相同、全部12首眼五文件与原运行SHA相同、R1重放全部五数组及NPZ SHA仍与原件完全一致。这是已保存数据验证，没有重新推进物理或创建任务。

`outputs/r3/v3/frozen/processes.json` 已complete/completed=true，正式12场全部exit0：3到达（F2_001、F3_002、F3_001）、9停车、0碰撞。多数场景未达到预期到达，锚点stress_v8也停车；这些真实结果保留，不调规则或换场景。E1阶段仍进行中：完整新拒绝候选反事实、复盘、每场保全与公开提交全部完成后，才进入E2。

E1正式运行终态时新增真实Lux任务24/170（22成功、2服务端失败），均终态。普通Python完成监督使用outputs/r3/v3/completion.json和outputs/qa/r3/final-completion-driver-v2.log。顺序为E1全部新拒绝CF与精确前缀核对、逐qpos复盘、每场完整外包与≤150MB公开manifest、E1summary；提交公开frozen-complete.json后才E2指定留出，随后同样保全、V1和最终D。提前的免费复盘/保全只读取已终态运行，完成内容会由监督直接复用；每run/scene锁避免并发写入。最终展示脚本尚未实际验收，不能把编译通过当作D完成。

## 新拒绝候选反事实的时间边界修正

F1_020 第4眼三份新拒绝候选都已实际执行并停车、无碰撞。初检查误用事件中四舍五入的103.96s，把干预后的第一个0.002s采样算进前缀，产生false；原失败检查完整保留。只读重核传感器 `t_sim=103.9579999999935`（包含观察时刻），全部5762样本的t/qpos/phase/control_actions/control_sources逐项相同，完整传感器qpos和该眼五份观测原字节也相同。修复只在R3 ops检查器，不改实验数组、src或R1/R2旧检查/证据，不重跑物理或创建任务。[诊断与旧/新核验](../../evidence/reviews/beforestep_r3/counterfactual-prefix-diagnostic.json)。

两条真实边界反例对应的单测已通过（允许干预后分歧；真正干预前分歧仍拒绝），命令 `python3 -m unittest discover -s tests -p test_r3_counterfactual_prefix.py -v`，2 tests/0.009s/exit0，日志outputs/qa/r3/final/prefix-boundary-tests.log。全部单测的最终验收仍待最终D执行。

早期v2全12真实复用尝试将单列完整表（8完成=7停车+1碰撞、4未完成），与最终v3并列，不能用v3安全结果覆盖旧碰撞；首页和相关工作同样明确版本范围。

<!-- R3-E1-COMPLETE-RUNS-START -->
## 最终v3：正式12场 summary 原文

以下为实际运行原summary，完整E1后处理与样本外E2仍需完成；眼数、时间和停车不能被解释成到达或速度收益。

### stress_v8

运行身份 `4909541f64eb4f2cb4dba2715248c46c`；正式driver退出码0。

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
  "execution_elapsed_s": 86.54,
  "sensor_mode": "live",
  "looks": 3,
  "final_pose": [
    4.044,
    0.496,
    -0.81
  ],
  "sim_time_s": 87.74,
  "wall_s": 399.4,
  "collision": null
}
```

### suite_r2_v4_F0_001

运行身份 `d29f081bbe354b40a563e9876f13a6e1`；正式driver退出码0。

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
  "scene_id": "suite_r2_v4_F0_001",
  "goal": [
    10.273944,
    -0.043551
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 53.38,
  "sensor_mode": "live",
  "looks": 2,
  "final_pose": [
    4.075,
    0.397,
    -0.2
  ],
  "sim_time_s": 54.58,
  "wall_s": 136.5,
  "collision": null
}
```

### suite_r2_v4_F0_005

运行身份 `f4f137935b14427c8d0320dc7c2bd185`；正式driver退出码0。

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
  "scene_id": "suite_r2_v4_F0_005",
  "goal": [
    10.305374,
    0.008717
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 51.8,
  "sensor_mode": "live",
  "looks": 2,
  "final_pose": [
    3.289,
    0.551,
    -43.77
  ],
  "sim_time_s": 53.0,
  "wall_s": 81.0,
  "collision": null
}
```

### suite_r2_v4_F1_001

运行身份 `1eb6e6e77f914cdc8c1c29d0efbd70f5`；正式driver退出码0。

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
  "scene_id": "suite_r2_v4_F1_001",
  "goal": [
    8.777473,
    0.01785
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 81.48,
  "sensor_mode": "live",
  "looks": 3,
  "final_pose": [
    8.081,
    -1.014,
    79.05
  ],
  "sim_time_s": 82.68,
  "wall_s": 1661.6,
  "collision": null
}
```

### suite_r2_v4_F1_020

运行身份 `0d59fb7b9ff54a9aaf0df55d19c26773`；正式driver退出码0。

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
  "execution_elapsed_s": 137.08,
  "sensor_mode": "live",
  "looks": 5,
  "final_pose": [
    6.425,
    -1.412,
    36.88
  ],
  "sim_time_s": 138.28,
  "wall_s": 769.6,
  "collision": null
}
```

### suite_r2_v4_F1_003

运行身份 `f95286df2a8947789eeaea8552f27962`；正式driver退出码0。

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
  "scene_id": "suite_r2_v4_F1_003",
  "goal": [
    9.095304,
    -0.071513
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 100.29,
  "sensor_mode": "live",
  "looks": 5,
  "final_pose": [
    8.681,
    2.008,
    -53.79
  ],
  "sim_time_s": 101.49,
  "wall_s": 546.8,
  "collision": null
}
```

### suite_r2_v4_F2_003

运行身份 `c504a985dee045099bb8d2cc3940dd1f`；正式driver退出码0。

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
  "scene_id": "suite_r2_v4_F2_003",
  "goal": [
    10.730404,
    0.01719
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 82.28,
  "sensor_mode": "live",
  "looks": 5,
  "final_pose": [
    4.266,
    1.995,
    38.74
  ],
  "sim_time_s": 83.48,
  "wall_s": 600.4,
  "collision": null
}
```

### suite_r2_v4_F2_007

运行身份 `6f83424271654501a8583c9d86c675c9`；正式driver退出码0。

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
  "scene_id": "suite_r2_v4_F2_007",
  "goal": [
    10.056258,
    0.005516
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 79.08,
  "sensor_mode": "live",
  "looks": 5,
  "final_pose": [
    4.252,
    2.007,
    -30.71
  ],
  "sim_time_s": 80.28,
  "wall_s": 368.9,
  "collision": null
}
```

### suite_r2_v4_F2_001

运行身份 `4e8125f3734444a4a82fa7be0fbac9d5`；正式driver退出码0。

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
  "scene_id": "suite_r2_v4_F2_001",
  "goal": [
    10.640641,
    -0.049459
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 117.37,
  "sensor_mode": "live",
  "looks": 4,
  "final_pose": [
    10.632,
    -0.05,
    20.37
  ],
  "sim_time_s": 118.57,
  "wall_s": 491.7,
  "collision": null
}
```

### suite_r2_v4_F3_002

运行身份 `379c9d5d0be64945a92ad0420d95c4b9`；正式driver退出码0。

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
  "scene_id": "suite_r2_v4_F3_002",
  "goal": [
    11.178607,
    -0.032265
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 175.51,
  "sensor_mode": "live",
  "looks": 4,
  "final_pose": [
    11.162,
    -0.022,
    31.41
  ],
  "sim_time_s": 176.71,
  "wall_s": 337.1,
  "collision": null
}
```

### suite_r2_v4_F3_004

运行身份 `ccfc1605a2834a82b77091dbe89840d2`；正式driver退出码0。

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
  "scene_id": "suite_r2_v4_F3_004",
  "goal": [
    10.771229,
    0.025802
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 16.9,
  "sensor_mode": "live",
  "looks": 1,
  "final_pose": [
    2.292,
    -0.5,
    -0.03
  ],
  "sim_time_s": 18.1,
  "wall_s": 81.5,
  "collision": null
}
```

### suite_r2_v4_F3_001

运行身份 `54dd8a71c12f4cfe9f1cea5214f43566`；正式driver退出码0。

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
  "scene_id": "suite_r2_v4_F3_001",
  "goal": [
    11.478607,
    -0.046403
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 142.23,
  "sensor_mode": "live",
  "looks": 5,
  "final_pose": [
    11.471,
    -0.049,
    24.66
  ],
  "sim_time_s": 143.43,
  "wall_s": 294.7,
  "collision": null
}
```

<!-- R3-E1-COMPLETE-RUNS-END -->

## E1免费复盘与已结束场景的保全核对

12个正式v3运行的XY与逐qpos三维复盘均已完成/exit0；早期4份复用，8份缺失记录补于独立sidecar，没有改原轨迹。11个已可保全的场景完成完整tar与≤150MB唯一manifest；F1_001等全部新拒绝CF终态后才保全，不能称E1全部完成。`PYTHONPATH=… python3 ops/verify_r3_custody.py --archives --out outputs/qa/r3/final/early-custody-audit.json` 实际exit0：11份manifest、1796个去重公开gzip对象全部解压SHA/大小正确，每个完整tar的全部条目逐项对原manifest SHA/大小相同。[薄核对回执](../../evidence/reviews/beforestep_r3/final-verification/early-custody-audit.json)。原GLB、旧v2失败与未完成尝试均纳入各场完整包，不删原件。

## 留出运行的预算边界与部分生成保全

ops预检查发现一批请求逐项创建，预算可能在中途用满：旧catch会直接结束，留下已知ID尚未查询；仅有look1_state也不足以证明首眼生成完整。R3-only收尾现在只查询已创建ID并下载原结果，缺失样本不创建，写独立lux_result.partial.json供完整scene包保存原GLB与输入；首眼generation仍pending时，strict明确未完成，不绕过首眼复用限制。src、170上限、截止时间、控制和观测规则均不变，正常完整请求原行为不变。

三条真正边界测试实际通过（3/0.065s/exit0）：169→170后一批第二份不创建，第一份原ID仅查询一次并留partial；已有观测但首眼生成未完不复用，后眼未完仍可复用完整首眼；无完整lux_result时已返回模型仍在完整tar内且SHA/原字节一致。[原日志](../../evidence/reviews/beforestep_r3/final-verification/partial-generation-tests.log)。此前全82已过；新增三条后，全85已实际通过（18.976s/exit0），[全套原日志](../../evidence/reviews/beforestep_r3/final-verification/final-unit-tests.log)。最终展示/公网验收仍待实验全部完成。

11场数据提交b754f16，947个LFS对象384MB实际上传完成；独立存储从origin下载947对象383711275bytes并逐Git pointer SHA/size核对全部通过。[远端回执](../../evidence/reviews/beforestep_r3/final-verification/early-publication-audit.json)。最后F1_001反事实仍在运行，E1阶段未完成。

原323项资产当前SHA再次实际核对通过：[回执](../../evidence/reviews/beforestep_r3/final-verification/core-assets.json)。新增报告整合前的本地文档链接检查通过，最终整合新增链接后再验收最终文档。

## E1完整本地收尾与阶段记录

正式12场3到达/9停车/0碰撞；新拒绝CF17/17全部实际执行，12到达/5停车/0碰撞，17前缀五数组/五观测/精确传感器pose全部相同。新CF结果只描述这批修订，原R2的17/102碰撞结论保持原字节。see-dark到达的9场中修订到达3场，已知场景复测没有全面替代黑影缺深度；停车更短不当作速度优势。

12份完整scene包与≤150MB唯一manifest全部实际完成，原22成功GLB均按SDK SHA保留，2服务端失败无GLB不当作自检拒绝；末场F1_001 10816文件/公开50.04MB/完整420.82MB。[完整保全回执](../../evidence/reviews/beforestep_r3/frozen-custody-audit.json)合并前11场与末场的实际tar逐文件SHA/大小、全部公开gzip字节核对，共2989去重publicobjects；[新增GLB保管回执](../../evidence/reviews/beforestep_r3/final-verification/e1-generated-assets.json)。source冻结4d53214、85单测已过，3995原R1R2受保护条目及全部原主结果不改。

当前新增24/170（22ok/2failed），累计192/360，全终态；E2尚未创建，监督等待公开阶段proof。先提交并核对末场新LFS可取，再发布frozen-complete.json，随后直接进入预先指定的留出顺序，不根据这批结果挑选新场景。最终报告、V1与D仍待完成，不作最终R3完成声明。

<!-- R3-RETAINED-SUMMARIES-START -->
## 其余保留运行 summary 原文

### suite_r2_v4_F1_001 CF look2_T2_B2

实际退出码0；干预与精确前缀验证通过。

```json
{
  "policy": "imagination_strict",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "stuck",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F1_001",
  "goal": [
    8.777473,
    0.01785
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 47.7,
  "sensor_mode": "live",
  "looks": 2,
  "final_pose": [
    5.092,
    -1.642,
    21.25
  ],
  "sim_time_s": 48.9,
  "wall_s": 131.3,
  "collision": null
}
```

### suite_r2_v4_F1_001 CF look2_T2_B1

实际退出码0；干预与精确前缀验证通过。

```json
{
  "policy": "imagination_strict",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "stuck",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F1_001",
  "goal": [
    8.777473,
    0.01785
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 47.7,
  "sensor_mode": "live",
  "looks": 2,
  "final_pose": [
    5.092,
    -1.642,
    21.25
  ],
  "sim_time_s": 48.9,
  "wall_s": 133.1,
  "collision": null
}
```

### suite_r2_v4_F1_001 CF look3_T3_A1

实际退出码0；干预与精确前缀验证通过。

```json
{
  "policy": "imagination_strict",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "arrived",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F1_001",
  "goal": [
    8.777473,
    0.01785
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 150.88,
  "sensor_mode": "live",
  "looks": 3,
  "final_pose": [
    8.785,
    0.017,
    163.39
  ],
  "sim_time_s": 152.08,
  "wall_s": 1025.3,
  "collision": null
}
```

### suite_r2_v4_F1_001 CF look3_T3_A2

实际退出码0；干预与精确前缀验证通过。

```json
{
  "policy": "imagination_strict",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "arrived",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F1_001",
  "goal": [
    8.777473,
    0.01785
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 150.88,
  "sensor_mode": "live",
  "looks": 3,
  "final_pose": [
    8.785,
    0.017,
    163.39
  ],
  "sim_time_s": 152.08,
  "wall_s": 964.8,
  "collision": null
}
```

### suite_r2_v4_F1_001 CF look3_T3_B1

实际退出码0；干预与精确前缀验证通过。

```json
{
  "policy": "imagination_strict",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "arrived",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F1_001",
  "goal": [
    8.777473,
    0.01785
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 137.52,
  "sensor_mode": "live",
  "looks": 3,
  "final_pose": [
    8.785,
    0.013,
    151.85
  ],
  "sim_time_s": 138.72,
  "wall_s": 969.2,
  "collision": null
}
```

### suite_r2_v4_F1_001 CF look3_T3_B2

实际退出码0；干预与精确前缀验证通过。

```json
{
  "policy": "imagination_strict",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "arrived",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F1_001",
  "goal": [
    8.777473,
    0.01785
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 137.82,
  "sensor_mode": "live",
  "looks": 3,
  "final_pose": [
    8.786,
    0.016,
    163.11
  ],
  "sim_time_s": 139.02,
  "wall_s": 1093.6,
  "collision": null
}
```

### suite_r2_v4_F1_001 CF look3_T3_C1

实际退出码0；干预与精确前缀验证通过。

```json
{
  "policy": "imagination_strict",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "arrived",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F1_001",
  "goal": [
    8.777473,
    0.01785
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 150.88,
  "sensor_mode": "live",
  "looks": 3,
  "final_pose": [
    8.785,
    0.017,
    163.39
  ],
  "sim_time_s": 152.08,
  "wall_s": 1095.6,
  "collision": null
}
```

### suite_r2_v4_F1_001 CF look3_T3_C2

实际退出码0；干预与精确前缀验证通过。

```json
{
  "policy": "imagination_strict",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "arrived",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F1_001",
  "goal": [
    8.777473,
    0.01785
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 150.88,
  "sensor_mode": "live",
  "looks": 3,
  "final_pose": [
    8.785,
    0.017,
    163.39
  ],
  "sim_time_s": 152.08,
  "wall_s": 1107.7,
  "collision": null
}
```

### suite_r2_v4_F1_001 CF look3_T3_A1b

实际退出码0；干预与精确前缀验证通过。

```json
{
  "policy": "imagination_strict",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "arrived",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F1_001",
  "goal": [
    8.777473,
    0.01785
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 150.88,
  "sensor_mode": "live",
  "looks": 3,
  "final_pose": [
    8.785,
    0.017,
    163.39
  ],
  "sim_time_s": 152.08,
  "wall_s": 990.1,
  "collision": null
}
```

### suite_r2_v4_F1_001 CF look3_T3_A2b

实际退出码0；干预与精确前缀验证通过。

```json
{
  "policy": "imagination_strict",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "arrived",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F1_001",
  "goal": [
    8.777473,
    0.01785
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 150.88,
  "sensor_mode": "live",
  "looks": 3,
  "final_pose": [
    8.785,
    0.017,
    163.39
  ],
  "sim_time_s": 152.08,
  "wall_s": 973.4,
  "collision": null
}
```

### suite_r2_v4_F1_001 CF look3_T3_B1b

实际退出码0；干预与精确前缀验证通过。

```json
{
  "policy": "imagination_strict",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "arrived",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F1_001",
  "goal": [
    8.777473,
    0.01785
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 150.88,
  "sensor_mode": "live",
  "looks": 3,
  "final_pose": [
    8.785,
    0.017,
    163.39
  ],
  "sim_time_s": 152.08,
  "wall_s": 996.7,
  "collision": null
}
```

### suite_r2_v4_F1_001 CF look3_T3_B2b

实际退出码0；干预与精确前缀验证通过。

```json
{
  "policy": "imagination_strict",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "arrived",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F1_001",
  "goal": [
    8.777473,
    0.01785
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 137.52,
  "sensor_mode": "live",
  "looks": 3,
  "final_pose": [
    8.785,
    0.013,
    151.85
  ],
  "sim_time_s": 138.72,
  "wall_s": 953.0,
  "collision": null
}
```

### suite_r2_v4_F1_001 CF look3_T3_C1b

实际退出码0；干预与精确前缀验证通过。

```json
{
  "policy": "imagination_strict",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "arrived",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F1_001",
  "goal": [
    8.777473,
    0.01785
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 150.88,
  "sensor_mode": "live",
  "looks": 3,
  "final_pose": [
    8.785,
    0.017,
    163.39
  ],
  "sim_time_s": 152.08,
  "wall_s": 980.7,
  "collision": null
}
```

### suite_r2_v4_F1_001 CF look3_T3_C2b

实际退出码0；干预与精确前缀验证通过。

```json
{
  "policy": "imagination_strict",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "arrived",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F1_001",
  "goal": [
    8.777473,
    0.01785
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 150.88,
  "sensor_mode": "live",
  "looks": 3,
  "final_pose": [
    8.785,
    0.017,
    163.39
  ],
  "sim_time_s": 152.08,
  "wall_s": 943.3,
  "collision": null
}
```

### suite_r2_v4_F1_020 CF look4_T3_B1

实际退出码0；干预与精确前缀验证通过。

```json
{
  "policy": "imagination_strict",
  "tag": "trusted",
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
  "execution_elapsed_s": 102.96,
  "sensor_mode": "live",
  "looks": 4,
  "final_pose": [
    3.475,
    -1.402,
    -7.35
  ],
  "sim_time_s": 104.16,
  "wall_s": 451.0,
  "collision": null
}
```

### suite_r2_v4_F1_020 CF look4_T3_A2

实际退出码0；干预与精确前缀验证通过。

```json
{
  "policy": "imagination_strict",
  "tag": "trusted",
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
  "execution_elapsed_s": 102.96,
  "sensor_mode": "live",
  "looks": 4,
  "final_pose": [
    3.475,
    -1.402,
    -7.35
  ],
  "sim_time_s": 104.16,
  "wall_s": 451.9,
  "collision": null
}
```

### suite_r2_v4_F1_020 CF look4_T3_B2

实际退出码0；干预与精确前缀验证通过。

```json
{
  "policy": "imagination_strict",
  "tag": "trusted",
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
  "execution_elapsed_s": 102.96,
  "sensor_mode": "live",
  "looks": 4,
  "final_pose": [
    3.475,
    -1.402,
    -7.35
  ],
  "sim_time_s": 104.16,
  "wall_s": 453.4,
  "collision": null
}
```

### 早期v2 stress_v8

早期真实任务复用，新增付费0；保持原失败/停车，不计样本外场景。

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
  "execution_elapsed_s": 141.0,
  "sensor_mode": "live",
  "looks": 5,
  "final_pose": [
    4.033,
    0.382,
    -7.39
  ],
  "sim_time_s": 142.2,
  "wall_s": 325.3,
  "collision": null
}
```

### 早期v2 suite_r2_v4_F1_020

早期真实任务复用，新增付费0；保持原失败/停车，不计样本外场景。

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
  "execution_elapsed_s": 127.92,
  "sensor_mode": "live",
  "looks": 5,
  "final_pose": [
    1.668,
    -0.789,
    4.69
  ],
  "sim_time_s": 129.12,
  "wall_s": 236.8,
  "collision": null
}
```

### 早期v2 suite_r2_v4_F1_003

早期真实任务复用，新增付费0；保持原失败/停车，不计样本外场景。

```json
{
  "policy": "imagination_strict",
  "tag": "imagination_strict",
  "see_dark": false,
  "imagine": "lux",
  "result": "collision",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F1_003",
  "goal": [
    9.095304,
    -0.071513
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 133.29,
  "sensor_mode": "live",
  "looks": 4,
  "final_pose": [
    8.093,
    1.515,
    -71.87
  ],
  "sim_time_s": 134.49,
  "wall_s": 188.1,
  "collision": {
    "body": "obstacle2",
    "robot_geom": null,
    "pos": [
      7.979,
      1.186,
      0.086
    ],
    "t": 134.486
  }
}
```

### 早期v2 suite_r2_v4_F2_003

早期真实任务复用，新增付费0；保持原失败/停车，不计样本外场景。

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
  "scene_id": "suite_r2_v4_F2_003",
  "goal": [
    10.730404,
    0.01719
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 81.86,
  "sensor_mode": "live",
  "looks": 5,
  "final_pose": [
    4.258,
    1.997,
    25.02
  ],
  "sim_time_s": 83.06,
  "wall_s": 282.4,
  "collision": null
}
```

### 早期v2 suite_r2_v4_F2_001

早期真实任务复用，新增付费0；保持原失败/停车，不计样本外场景。

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
  "scene_id": "suite_r2_v4_F2_001",
  "goal": [
    10.640641,
    -0.049459
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 82.23,
  "sensor_mode": "live",
  "looks": 5,
  "final_pose": [
    4.267,
    1.997,
    38.67
  ],
  "sim_time_s": 83.43,
  "wall_s": 241.9,
  "collision": null
}
```

### 早期v2 suite_r2_v4_F3_004

早期真实任务复用，新增付费0；保持原失败/停车，不计样本外场景。

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
  "scene_id": "suite_r2_v4_F3_004",
  "goal": [
    10.771229,
    0.025802
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 16.9,
  "sensor_mode": "live",
  "looks": 1,
  "final_pose": [
    2.292,
    -0.5,
    -0.03
  ],
  "sim_time_s": 18.1,
  "wall_s": 87.4,
  "collision": null
}
```

### 早期v2 suite_r2_v4_F3_001

早期真实任务复用，新增付费0；保持原失败/停车，不计样本外场景。

```json
{
  "policy": "imagination_strict",
  "tag": "imagination_strict",
  "see_dark": false,
  "imagine": "lux",
  "result": "stopped_short",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F3_001",
  "goal": [
    11.478607,
    -0.046403
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 110.63,
  "sensor_mode": "live",
  "looks": 2,
  "final_pose": [
    9.332,
    -0.06,
    98.68
  ],
  "sim_time_s": 111.83,
  "wall_s": 94.3,
  "collision": null
}
```

### 早期v2 suite_r2_v4_F3_002

早期真实任务复用，新增付费0；保持原失败/停车，不计样本外场景。

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
  "scene_id": "suite_r2_v4_F3_002",
  "goal": [
    11.178607,
    -0.032265
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 217.28,
  "sensor_mode": "live",
  "looks": 5,
  "final_pose": [
    8.259,
    1.205,
    -110.84
  ],
  "sim_time_s": 218.48,
  "wall_s": 257.7,
  "collision": null
}
```

### v1离线替身 stress_v8 truth

离线替身，新增付费0；原预期未通过，保留原件与诊断。

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
  "execution_elapsed_s": 115.48,
  "sensor_mode": "live",
  "looks": 4,
  "final_pose": [
    3.871,
    0.182,
    -3.23
  ],
  "sim_time_s": 116.68,
  "wall_s": 60.2,
  "collision": null
}
```

### v1离线替身 stress_v8 registered

离线替身，新增付费0；原预期未通过，保留原件与诊断。

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
  "execution_elapsed_s": 111.34,
  "sensor_mode": "live",
  "looks": 4,
  "final_pose": [
    3.654,
    0.333,
    -11.28
  ],
  "sim_time_s": 112.54,
  "wall_s": 211.6,
  "collision": null
}
```

### v1离线替身 suite_r2_v4_F1_020 truth

离线替身，新增付费0；原预期未通过，保留原件与诊断。

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
  "execution_elapsed_s": 16.9,
  "sensor_mode": "live",
  "looks": 1,
  "final_pose": [
    2.292,
    -0.5,
    0.04
  ],
  "sim_time_s": 18.1,
  "wall_s": 24.1,
  "collision": null
}
```

### v1离线替身 suite_r2_v4_F1_020 registered

离线替身，新增付费0；原预期未通过，保留原件与诊断。

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
  "wall_s": 159.3,
  "collision": null
}
```

<!-- R3-RETAINED-SUMMARIES-END -->

## E1公开完成，进入固定E2

E1数据f971519已实际push：1137末场新LFS对象46MB上传成功；再次只从origin下载到独立存储，1137对象45874439bytes逐Git pointer SHA/size核对全pass/exit0。[末场远端回执](../../evidence/reviews/beforestep_r3/final-verification/last-frozen-publication-audit.json)。加前947对象383711275bytes，已公开新增2084对象429585714bytes，全部分两次独立远端验证；本地旧缓存未用于证明远端下载。

[公开E1阶段证明](../../evidence/reviews/beforestep_r3/frozen-complete.json)附全12原summary、逐首眼byte核对、17CF精确前缀、每场manifest SHA和完整tar核对/远端回执。监督验证这份证明已在远端main后才自动运行E2：F0_002、F2_011、F3_005，预算尚余146时继续F0_003、F3_006。E1已完成不是整个R3完成；继续E2、V1、D，不等确认。

<!-- R3-E2-BEGIN -->
## E2固定留出已经启动

监督已确认E1阶段证明454951a在远端main后，开始F0_002，后续按F2_011/F3_005/预算余F0_003/F3_006固定次序。第一场四个当前源码基线均exit0：conservative停车、see-dark停车、optimistic碰撞、truth到达；与选择时的旧分布标签并列，不因为当前see-dark停车而更换场景。原想象正在真实首眼配准/自检，尚无终态；strict随后只复用同byte首眼。当前R3新36/170（32ok/4providerfailed），全终态，其中本场新增12（10ok/2failed），不能把生成返回或配准产出当作通行结果。

### E2 suite_r2_v4_F0_002 conservative summary原文

```json
{
  "policy": "conservative",
  "tag": "conservative",
  "see_dark": false,
  "imagine": null,
  "result": "stuck",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F0_002",
  "goal": [
    10.301463,
    -0.045753
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 142.0,
  "sensor_mode": "live",
  "looks": 5,
  "final_pose": [
    4.077,
    0.214,
    -8.08
  ],
  "sim_time_s": 143.2,
  "wall_s": 72.7,
  "collision": null
}
```

### E2 suite_r2_v4_F0_002 see_dark summary原文

```json
{
  "policy": "conservative",
  "tag": "see_dark",
  "see_dark": true,
  "imagine": null,
  "result": "stuck",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F0_002",
  "goal": [
    10.301463,
    -0.045753
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 92.44,
  "sensor_mode": "live",
  "looks": 3,
  "final_pose": [
    5.663,
    -0.597,
    17.28
  ],
  "sim_time_s": 93.64,
  "wall_s": 57.7,
  "collision": null
}
```

### E2 suite_r2_v4_F0_002 optimistic summary原文

```json
{
  "policy": "optimistic",
  "tag": "optimistic",
  "see_dark": false,
  "imagine": null,
  "result": "collision",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F0_002",
  "goal": [
    10.301463,
    -0.045753
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 79.73,
  "sensor_mode": "live",
  "looks": 1,
  "final_pose": [
    6.934,
    -0.557,
    3.54
  ],
  "sim_time_s": 80.93,
  "wall_s": 48.7,
  "collision": {
    "body": "obstacle1",
    "robot_geom": null,
    "pos": [
      7.189,
      -0.325,
      0.121
    ],
    "t": 80.934
  }
}
```

### E2 suite_r2_v4_F0_002 truth summary原文

```json
{
  "policy": "imagination",
  "tag": "truth",
  "see_dark": false,
  "imagine": "truth",
  "result": "arrived",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F0_002",
  "goal": [
    10.301463,
    -0.045753
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 113.76,
  "sensor_mode": "live",
  "looks": 1,
  "final_pose": [
    10.294,
    -0.048,
    18.05
  ],
  "sim_time_s": 114.96,
  "wall_s": 55.6,
  "collision": null
}
```

<!-- R3-E2-BASELINES-F0-002-END -->

## E2 F0_002六栏实际终态

本场四baseline及原/strict真实链全部complete，orig和strict均2眼54.52s停车/0coll，首眼五文件与原方法逐byte相同；严格版本后眼相同请求复用已知SDK身份，没有重建任务。当前48新任务43ok5providerfailed，下一场F2_011按固定次序继续，首场两policy新拒绝CF提前用单worker与标准路径验证。仍不能以停车短时间解释效率或到达收益。

### E2 suite_r2_v4_F0_002 imagination summary原文

```json
{
  "policy": "imagination",
  "tag": "imagination",
  "see_dark": false,
  "imagine": "lux",
  "result": "stuck",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F0_002",
  "goal": [
    10.301463,
    -0.045753
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 53.32,
  "sensor_mode": "live",
  "looks": 2,
  "final_pose": [
    4.276,
    0.398,
    -1.17
  ],
  "sim_time_s": 54.52,
  "wall_s": 1008.9,
  "collision": null
}
```

### E2 suite_r2_v4_F0_002 imagination_strict summary原文

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
  "scene_id": "suite_r2_v4_F0_002",
  "goal": [
    10.301463,
    -0.045753
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 53.32,
  "sensor_mode": "live",
  "looks": 2,
  "final_pose": [
    4.276,
    0.398,
    -1.17
  ],
  "sim_time_s": 54.52,
  "wall_s": 91.3,
  "collision": null
}
```

## 留出监督恢复与 V1 本地验证

2026-11-11 16:26 UTC 实核旧 supervisor 与 F2_011 子进程已不在进程表，退出原因未确定；原未完成目录及 ledger 已保留为该场 `interrupted-20261111T162616Z/`。从同场同来源和已知任务恢复，未重建首眼、未重付费。新监督进程独立于会话，后续反事实单 worker，以降低并发物理内存峰值；`src/` 不变。恢复时本轮60任务全部终态55成功/5服务商失败。

V1已加入锚点、F1_020、F3_004三份最终v3修订原运行，索引现22运行、1544独立公开byte对象。`ops/build_video_index.py` 同时复用已公开R3 scene清单，`ops/check_video_index.py` 实際 exit0；所有指定观测、world网格、候选指标、预演、复盘与渲染资产均存在且原SHA相同。105份新公开路径共139830523bytes待推送验证；完整数据仍保留。这里只生成数据索引，没有渲染视频。日志 `outputs/qa/r3/video-index-early.log` 与 `video-index-early-check.log`。

V1远端实际确认：`b00edc0c97f29cc790da279b547707e11a2e8a19`已push，独立storage下载video/assets公开namespace的306份LFS共407763387bytes，每个Git pointer SHA及size通过。R3场景复用对象的独立下载验证仍见E1公开保全audit。证据 [video-publication-audit.json](../../evidence/reviews/beforestep_r3/final-verification/video-publication-audit.json)；V1现在完成，E2/D继续。

### E2 suite_r2_v4_F2_011 optimistic summary原文

原运行 `outputs/r3/v3/holdouts/suite_r2_v4_F2_011/baselines/optimistic`；exit0，当前源码与冻结来源一致。

```json
{
  "policy": "optimistic",
  "tag": "optimistic",
  "see_dark": false,
  "imagine": null,
  "result": "collision",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F2_011",
  "goal": [
    10.564532,
    -0.007639
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 80.71,
  "sensor_mode": "live",
  "looks": 1,
  "final_pose": [
    6.901,
    -0.342,
    4.35
  ],
  "sim_time_s": 81.91,
  "wall_s": 38.9,
  "collision": {
    "body": "obstacle1",
    "robot_geom": null,
    "pos": [
      7.151,
      -0.106,
      0.12
    ],
    "t": 81.908
  }
}
```

### E2 suite_r2_v4_F2_011 conservative summary原文

原运行 `outputs/r3/v3/holdouts/suite_r2_v4_F2_011/baselines/conservative`；exit0，当前源码与冻结来源一致。

```json
{
  "policy": "conservative",
  "tag": "conservative",
  "see_dark": false,
  "imagine": null,
  "result": "stuck",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F2_011",
  "goal": [
    10.564532,
    -0.007639
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 81.06,
  "sensor_mode": "live",
  "looks": 5,
  "final_pose": [
    4.26,
    1.993,
    28.04
  ],
  "sim_time_s": 82.26,
  "wall_s": 53.1,
  "collision": null
}
```

### E2 suite_r2_v4_F2_011 see_dark summary原文

原运行 `outputs/r3/v3/holdouts/suite_r2_v4_F2_011/baselines/see_dark`；exit0，当前源码与冻结来源一致。

```json
{
  "policy": "conservative",
  "tag": "see_dark",
  "see_dark": true,
  "imagine": null,
  "result": "stuck",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F2_011",
  "goal": [
    10.564532,
    -0.007639
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 80.77,
  "sensor_mode": "live",
  "looks": 5,
  "final_pose": [
    4.265,
    1.995,
    29.93
  ],
  "sim_time_s": 81.97,
  "wall_s": 55.7,
  "collision": null
}
```

### E2 suite_r2_v4_F2_011 truth summary原文

原运行 `outputs/r3/v3/holdouts/suite_r2_v4_F2_011/baselines/truth`；exit0，当前源码与冻结来源一致。

```json
{
  "policy": "imagination",
  "tag": "truth",
  "see_dark": false,
  "imagine": "truth",
  "result": "arrived",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F2_011",
  "goal": [
    10.564532,
    -0.007639
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 114.22,
  "sensor_mode": "live",
  "looks": 1,
  "final_pose": [
    10.557,
    -0.007,
    13.33
  ],
  "sim_time_s": 115.42,
  "wall_s": 56.8,
  "collision": null
}
```

最终验收单测已在恢复及V1改动后实际运行：`python3 -m unittest discover -s tests -v`，exit0，85项/11.751s全部通过。[原日志](../../evidence/reviews/beforestep_r3/final-verification/unit-tests-after-video-recovery.log)。后续源码没有变化时不重复昂贵物理回归；最终数字/文档/页面验收仍待全部实验与保全终态。

## E2 F0_002新增拒绝反事实实际完成

两种方法各19份，共38次干预（共用首眼候选可能在两policy下分别干预，不能当作38个独立生成样本）。原方法17到达/2停车，strict19停车，均0碰撞；全部5轨迹数组及捕获时刻5观测字节前缀通过。只对本轮新生成且被拒的候选执行，未重复R1/R2拒绝候选。完整scene包与唯一SHA清单正在保全。

### E2 CF suite_r2_v4_F0_002 imagination look1_T1_C1 summary原文

原运行 `outputs/r3/v3/counterfactuals/suite_r2_v4_F0_002/imagination/look1_T1_C1/trusted`；exit0，干预及前缀验证pass。

```json
{
  "policy": "imagination",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "stuck",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F0_002",
  "goal": [
    10.301463,
    -0.045753
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 16.88,
  "sensor_mode": "live",
  "looks": 1,
  "final_pose": [
    2.292,
    -0.5,
    0.04
  ],
  "sim_time_s": 18.08,
  "wall_s": 38.8,
  "collision": null
}
```

### E2 CF suite_r2_v4_F0_002 imagination look1_T1_C2 summary原文

原运行 `outputs/r3/v3/counterfactuals/suite_r2_v4_F0_002/imagination/look1_T1_C2/trusted`；exit0，干预及前缀验证pass。

```json
{
  "policy": "imagination",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "stuck",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F0_002",
  "goal": [
    10.301463,
    -0.045753
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 16.88,
  "sensor_mode": "live",
  "looks": 1,
  "final_pose": [
    2.292,
    -0.5,
    0.04
  ],
  "sim_time_s": 18.08,
  "wall_s": 39.8,
  "collision": null
}
```

### E2 CF suite_r2_v4_F0_002 imagination look1_T2_A1 summary原文

原运行 `outputs/r3/v3/counterfactuals/suite_r2_v4_F0_002/imagination/look1_T2_A1/trusted`；exit0，干预及前缀验证pass。

```json
{
  "policy": "imagination",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "arrived",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F0_002",
  "goal": [
    10.301463,
    -0.045753
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 101.7,
  "sensor_mode": "live",
  "looks": 1,
  "final_pose": [
    10.294,
    -0.046,
    12.06
  ],
  "sim_time_s": 102.9,
  "wall_s": 60.5,
  "collision": null
}
```

### E2 CF suite_r2_v4_F0_002 imagination look1_T2_A2 summary原文

原运行 `outputs/r3/v3/counterfactuals/suite_r2_v4_F0_002/imagination/look1_T2_A2/trusted`；exit0，干预及前缀验证pass。

```json
{
  "policy": "imagination",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "arrived",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F0_002",
  "goal": [
    10.301463,
    -0.045753
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 101.7,
  "sensor_mode": "live",
  "looks": 1,
  "final_pose": [
    10.294,
    -0.046,
    12.06
  ],
  "sim_time_s": 102.9,
  "wall_s": 61.8,
  "collision": null
}
```

### E2 CF suite_r2_v4_F0_002 imagination look1_T2_B1 summary原文

原运行 `outputs/r3/v3/counterfactuals/suite_r2_v4_F0_002/imagination/look1_T2_B1/trusted`；exit0，干预及前缀验证pass。

```json
{
  "policy": "imagination",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "arrived",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F0_002",
  "goal": [
    10.301463,
    -0.045753
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 101.7,
  "sensor_mode": "live",
  "looks": 1,
  "final_pose": [
    10.294,
    -0.046,
    12.06
  ],
  "sim_time_s": 102.9,
  "wall_s": 57.4,
  "collision": null
}
```

### E2 CF suite_r2_v4_F0_002 imagination look1_T2_B2 summary原文

原运行 `outputs/r3/v3/counterfactuals/suite_r2_v4_F0_002/imagination/look1_T2_B2/trusted`；exit0，干预及前缀验证pass。

```json
{
  "policy": "imagination",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "arrived",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F0_002",
  "goal": [
    10.301463,
    -0.045753
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 101.7,
  "sensor_mode": "live",
  "looks": 1,
  "final_pose": [
    10.294,
    -0.046,
    12.06
  ],
  "sim_time_s": 102.9,
  "wall_s": 67.0,
  "collision": null
}
```

### E2 CF suite_r2_v4_F0_002 imagination look1_T2_C1 summary原文

原运行 `outputs/r3/v3/counterfactuals/suite_r2_v4_F0_002/imagination/look1_T2_C1/trusted`；exit0，干预及前缀验证pass。

```json
{
  "policy": "imagination",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "arrived",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F0_002",
  "goal": [
    10.301463,
    -0.045753
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 101.7,
  "sensor_mode": "live",
  "looks": 1,
  "final_pose": [
    10.294,
    -0.046,
    12.06
  ],
  "sim_time_s": 102.9,
  "wall_s": 65.6,
  "collision": null
}
```

### E2 CF suite_r2_v4_F0_002 imagination look1_T2_C2 summary原文

原运行 `outputs/r3/v3/counterfactuals/suite_r2_v4_F0_002/imagination/look1_T2_C2/trusted`；exit0，干预及前缀验证pass。

```json
{
  "policy": "imagination",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "arrived",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F0_002",
  "goal": [
    10.301463,
    -0.045753
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 101.7,
  "sensor_mode": "live",
  "looks": 1,
  "final_pose": [
    10.294,
    -0.046,
    12.06
  ],
  "sim_time_s": 102.9,
  "wall_s": 62.4,
  "collision": null
}
```

### E2 CF suite_r2_v4_F0_002 imagination look2_T2_A1 summary原文

原运行 `outputs/r3/v3/counterfactuals/suite_r2_v4_F0_002/imagination/look2_T2_A1/trusted`；exit0，干预及前缀验证pass。

```json
{
  "policy": "imagination",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "arrived",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F0_002",
  "goal": [
    10.301463,
    -0.045753
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 126.8,
  "sensor_mode": "live",
  "looks": 2,
  "final_pose": [
    10.294,
    -0.047,
    17.33
  ],
  "sim_time_s": 128.0,
  "wall_s": 93.9,
  "collision": null
}
```

### E2 CF suite_r2_v4_F0_002 imagination look2_T2_A2 summary原文

原运行 `outputs/r3/v3/counterfactuals/suite_r2_v4_F0_002/imagination/look2_T2_A2/trusted`；exit0，干预及前缀验证pass。

```json
{
  "policy": "imagination",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "arrived",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F0_002",
  "goal": [
    10.301463,
    -0.045753
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 126.8,
  "sensor_mode": "live",
  "looks": 2,
  "final_pose": [
    10.294,
    -0.047,
    17.33
  ],
  "sim_time_s": 128.0,
  "wall_s": 93.6,
  "collision": null
}
```

### E2 CF suite_r2_v4_F0_002 imagination look2_T2_B1 summary原文

原运行 `outputs/r3/v3/counterfactuals/suite_r2_v4_F0_002/imagination/look2_T2_B1/trusted`；exit0，干预及前缀验证pass。

```json
{
  "policy": "imagination",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "arrived",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F0_002",
  "goal": [
    10.301463,
    -0.045753
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 126.8,
  "sensor_mode": "live",
  "looks": 2,
  "final_pose": [
    10.294,
    -0.047,
    17.33
  ],
  "sim_time_s": 128.0,
  "wall_s": 97.4,
  "collision": null
}
```

### E2 CF suite_r2_v4_F0_002 imagination look2_T2_B2 summary原文

原运行 `outputs/r3/v3/counterfactuals/suite_r2_v4_F0_002/imagination/look2_T2_B2/trusted`；exit0，干预及前缀验证pass。

```json
{
  "policy": "imagination",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "arrived",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F0_002",
  "goal": [
    10.301463,
    -0.045753
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 127.28,
  "sensor_mode": "live",
  "looks": 2,
  "final_pose": [
    10.292,
    -0.046,
    18.87
  ],
  "sim_time_s": 128.48,
  "wall_s": 96.2,
  "collision": null
}
```

### E2 CF suite_r2_v4_F0_002 imagination look2_T2_C1 summary原文

原运行 `outputs/r3/v3/counterfactuals/suite_r2_v4_F0_002/imagination/look2_T2_C1/trusted`；exit0，干预及前缀验证pass。

```json
{
  "policy": "imagination",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "arrived",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F0_002",
  "goal": [
    10.301463,
    -0.045753
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 126.8,
  "sensor_mode": "live",
  "looks": 2,
  "final_pose": [
    10.294,
    -0.047,
    17.33
  ],
  "sim_time_s": 128.0,
  "wall_s": 87.1,
  "collision": null
}
```

### E2 CF suite_r2_v4_F0_002 imagination look2_T2_C2 summary原文

原运行 `outputs/r3/v3/counterfactuals/suite_r2_v4_F0_002/imagination/look2_T2_C2/trusted`；exit0，干预及前缀验证pass。

```json
{
  "policy": "imagination",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "arrived",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F0_002",
  "goal": [
    10.301463,
    -0.045753
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 126.8,
  "sensor_mode": "live",
  "looks": 2,
  "final_pose": [
    10.294,
    -0.047,
    17.33
  ],
  "sim_time_s": 128.0,
  "wall_s": 86.5,
  "collision": null
}
```

### E2 CF suite_r2_v4_F0_002 imagination look2_T2_A1b summary原文

原运行 `outputs/r3/v3/counterfactuals/suite_r2_v4_F0_002/imagination/look2_T2_A1b/trusted`；exit0，干预及前缀验证pass。

```json
{
  "policy": "imagination",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "arrived",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F0_002",
  "goal": [
    10.301463,
    -0.045753
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 126.8,
  "sensor_mode": "live",
  "looks": 2,
  "final_pose": [
    10.294,
    -0.047,
    17.33
  ],
  "sim_time_s": 128.0,
  "wall_s": 87.1,
  "collision": null
}
```

### E2 CF suite_r2_v4_F0_002 imagination look2_T2_A2b summary原文

原运行 `outputs/r3/v3/counterfactuals/suite_r2_v4_F0_002/imagination/look2_T2_A2b/trusted`；exit0，干预及前缀验证pass。

```json
{
  "policy": "imagination",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "arrived",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F0_002",
  "goal": [
    10.301463,
    -0.045753
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 126.8,
  "sensor_mode": "live",
  "looks": 2,
  "final_pose": [
    10.294,
    -0.047,
    17.33
  ],
  "sim_time_s": 128.0,
  "wall_s": 86.4,
  "collision": null
}
```

### E2 CF suite_r2_v4_F0_002 imagination look2_T2_B1b summary原文

原运行 `outputs/r3/v3/counterfactuals/suite_r2_v4_F0_002/imagination/look2_T2_B1b/trusted`；exit0，干预及前缀验证pass。

```json
{
  "policy": "imagination",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "arrived",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F0_002",
  "goal": [
    10.301463,
    -0.045753
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 126.8,
  "sensor_mode": "live",
  "looks": 2,
  "final_pose": [
    10.294,
    -0.047,
    17.33
  ],
  "sim_time_s": 128.0,
  "wall_s": 86.3,
  "collision": null
}
```

### E2 CF suite_r2_v4_F0_002 imagination look2_T2_C1b summary原文

原运行 `outputs/r3/v3/counterfactuals/suite_r2_v4_F0_002/imagination/look2_T2_C1b/trusted`；exit0，干预及前缀验证pass。

```json
{
  "policy": "imagination",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "arrived",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F0_002",
  "goal": [
    10.301463,
    -0.045753
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 126.8,
  "sensor_mode": "live",
  "looks": 2,
  "final_pose": [
    10.294,
    -0.047,
    17.33
  ],
  "sim_time_s": 128.0,
  "wall_s": 87.9,
  "collision": null
}
```

### E2 CF suite_r2_v4_F0_002 imagination look2_T2_C2b summary原文

原运行 `outputs/r3/v3/counterfactuals/suite_r2_v4_F0_002/imagination/look2_T2_C2b/trusted`；exit0，干预及前缀验证pass。

```json
{
  "policy": "imagination",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "arrived",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F0_002",
  "goal": [
    10.301463,
    -0.045753
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 126.8,
  "sensor_mode": "live",
  "looks": 2,
  "final_pose": [
    10.294,
    -0.047,
    17.33
  ],
  "sim_time_s": 128.0,
  "wall_s": 92.2,
  "collision": null
}
```

### E2 CF suite_r2_v4_F0_002 imagination_strict look1_T1_C1 summary原文

原运行 `outputs/r3/v3/counterfactuals/suite_r2_v4_F0_002/imagination_strict/look1_T1_C1/trusted`；exit0，干预及前缀验证pass。

```json
{
  "policy": "imagination_strict",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "stuck",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F0_002",
  "goal": [
    10.301463,
    -0.045753
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 16.88,
  "sensor_mode": "live",
  "looks": 1,
  "final_pose": [
    2.292,
    -0.5,
    0.04
  ],
  "sim_time_s": 18.08,
  "wall_s": 46.9,
  "collision": null
}
```

### E2 CF suite_r2_v4_F0_002 imagination_strict look1_T1_C2 summary原文

原运行 `outputs/r3/v3/counterfactuals/suite_r2_v4_F0_002/imagination_strict/look1_T1_C2/trusted`；exit0，干预及前缀验证pass。

```json
{
  "policy": "imagination_strict",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "stuck",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F0_002",
  "goal": [
    10.301463,
    -0.045753
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 16.88,
  "sensor_mode": "live",
  "looks": 1,
  "final_pose": [
    2.292,
    -0.5,
    0.04
  ],
  "sim_time_s": 18.08,
  "wall_s": 54.1,
  "collision": null
}
```

### E2 CF suite_r2_v4_F0_002 imagination_strict look1_T2_A1 summary原文

原运行 `outputs/r3/v3/counterfactuals/suite_r2_v4_F0_002/imagination_strict/look1_T2_A1/trusted`；exit0，干预及前缀验证pass。

```json
{
  "policy": "imagination_strict",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "stuck",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F0_002",
  "goal": [
    10.301463,
    -0.045753
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 16.88,
  "sensor_mode": "live",
  "looks": 1,
  "final_pose": [
    2.292,
    -0.5,
    0.04
  ],
  "sim_time_s": 18.08,
  "wall_s": 54.0,
  "collision": null
}
```

### E2 CF suite_r2_v4_F0_002 imagination_strict look1_T2_A2 summary原文

原运行 `outputs/r3/v3/counterfactuals/suite_r2_v4_F0_002/imagination_strict/look1_T2_A2/trusted`；exit0，干预及前缀验证pass。

```json
{
  "policy": "imagination_strict",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "stuck",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F0_002",
  "goal": [
    10.301463,
    -0.045753
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 16.88,
  "sensor_mode": "live",
  "looks": 1,
  "final_pose": [
    2.292,
    -0.5,
    0.04
  ],
  "sim_time_s": 18.08,
  "wall_s": 54.0,
  "collision": null
}
```

### E2 CF suite_r2_v4_F0_002 imagination_strict look1_T2_B1 summary原文

原运行 `outputs/r3/v3/counterfactuals/suite_r2_v4_F0_002/imagination_strict/look1_T2_B1/trusted`；exit0，干预及前缀验证pass。

```json
{
  "policy": "imagination_strict",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "stuck",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F0_002",
  "goal": [
    10.301463,
    -0.045753
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 16.88,
  "sensor_mode": "live",
  "looks": 1,
  "final_pose": [
    2.292,
    -0.5,
    0.04
  ],
  "sim_time_s": 18.08,
  "wall_s": 53.1,
  "collision": null
}
```

### E2 CF suite_r2_v4_F0_002 imagination_strict look1_T2_B2 summary原文

原运行 `outputs/r3/v3/counterfactuals/suite_r2_v4_F0_002/imagination_strict/look1_T2_B2/trusted`；exit0，干预及前缀验证pass。

```json
{
  "policy": "imagination_strict",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "stuck",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F0_002",
  "goal": [
    10.301463,
    -0.045753
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 16.88,
  "sensor_mode": "live",
  "looks": 1,
  "final_pose": [
    2.292,
    -0.5,
    0.04
  ],
  "sim_time_s": 18.08,
  "wall_s": 53.5,
  "collision": null
}
```

### E2 CF suite_r2_v4_F0_002 imagination_strict look1_T2_C1 summary原文

原运行 `outputs/r3/v3/counterfactuals/suite_r2_v4_F0_002/imagination_strict/look1_T2_C1/trusted`；exit0，干预及前缀验证pass。

```json
{
  "policy": "imagination_strict",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "stuck",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F0_002",
  "goal": [
    10.301463,
    -0.045753
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 16.88,
  "sensor_mode": "live",
  "looks": 1,
  "final_pose": [
    2.292,
    -0.5,
    0.04
  ],
  "sim_time_s": 18.08,
  "wall_s": 57.9,
  "collision": null
}
```

### E2 CF suite_r2_v4_F0_002 imagination_strict look1_T2_C2 summary原文

原运行 `outputs/r3/v3/counterfactuals/suite_r2_v4_F0_002/imagination_strict/look1_T2_C2/trusted`；exit0，干预及前缀验证pass。

```json
{
  "policy": "imagination_strict",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "stuck",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F0_002",
  "goal": [
    10.301463,
    -0.045753
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 16.88,
  "sensor_mode": "live",
  "looks": 1,
  "final_pose": [
    2.292,
    -0.5,
    0.04
  ],
  "sim_time_s": 18.08,
  "wall_s": 49.9,
  "collision": null
}
```

### E2 CF suite_r2_v4_F0_002 imagination_strict look2_T2_A1 summary原文

原运行 `outputs/r3/v3/counterfactuals/suite_r2_v4_F0_002/imagination_strict/look2_T2_A1/trusted`；exit0，干预及前缀验证pass。

```json
{
  "policy": "imagination_strict",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "stuck",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F0_002",
  "goal": [
    10.301463,
    -0.045753
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 53.32,
  "sensor_mode": "live",
  "looks": 2,
  "final_pose": [
    4.276,
    0.398,
    -1.17
  ],
  "sim_time_s": 54.52,
  "wall_s": 100.6,
  "collision": null
}
```

### E2 CF suite_r2_v4_F0_002 imagination_strict look2_T2_A2 summary原文

原运行 `outputs/r3/v3/counterfactuals/suite_r2_v4_F0_002/imagination_strict/look2_T2_A2/trusted`；exit0，干预及前缀验证pass。

```json
{
  "policy": "imagination_strict",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "stuck",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F0_002",
  "goal": [
    10.301463,
    -0.045753
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 53.32,
  "sensor_mode": "live",
  "looks": 2,
  "final_pose": [
    4.276,
    0.398,
    -1.17
  ],
  "sim_time_s": 54.52,
  "wall_s": 100.0,
  "collision": null
}
```

### E2 CF suite_r2_v4_F0_002 imagination_strict look2_T2_B1 summary原文

原运行 `outputs/r3/v3/counterfactuals/suite_r2_v4_F0_002/imagination_strict/look2_T2_B1/trusted`；exit0，干预及前缀验证pass。

```json
{
  "policy": "imagination_strict",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "stuck",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F0_002",
  "goal": [
    10.301463,
    -0.045753
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 53.32,
  "sensor_mode": "live",
  "looks": 2,
  "final_pose": [
    4.276,
    0.398,
    -1.17
  ],
  "sim_time_s": 54.52,
  "wall_s": 99.3,
  "collision": null
}
```

### E2 CF suite_r2_v4_F0_002 imagination_strict look2_T2_B2 summary原文

原运行 `outputs/r3/v3/counterfactuals/suite_r2_v4_F0_002/imagination_strict/look2_T2_B2/trusted`；exit0，干预及前缀验证pass。

```json
{
  "policy": "imagination_strict",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "stuck",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F0_002",
  "goal": [
    10.301463,
    -0.045753
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 53.32,
  "sensor_mode": "live",
  "looks": 2,
  "final_pose": [
    4.276,
    0.398,
    -1.17
  ],
  "sim_time_s": 54.52,
  "wall_s": 101.8,
  "collision": null
}
```

### E2 CF suite_r2_v4_F0_002 imagination_strict look2_T2_C1 summary原文

原运行 `outputs/r3/v3/counterfactuals/suite_r2_v4_F0_002/imagination_strict/look2_T2_C1/trusted`；exit0，干预及前缀验证pass。

```json
{
  "policy": "imagination_strict",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "stuck",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F0_002",
  "goal": [
    10.301463,
    -0.045753
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 53.32,
  "sensor_mode": "live",
  "looks": 2,
  "final_pose": [
    4.276,
    0.398,
    -1.17
  ],
  "sim_time_s": 54.52,
  "wall_s": 100.3,
  "collision": null
}
```

### E2 CF suite_r2_v4_F0_002 imagination_strict look2_T2_C2 summary原文

原运行 `outputs/r3/v3/counterfactuals/suite_r2_v4_F0_002/imagination_strict/look2_T2_C2/trusted`；exit0，干预及前缀验证pass。

```json
{
  "policy": "imagination_strict",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "stuck",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F0_002",
  "goal": [
    10.301463,
    -0.045753
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 53.32,
  "sensor_mode": "live",
  "looks": 2,
  "final_pose": [
    4.276,
    0.398,
    -1.17
  ],
  "sim_time_s": 54.52,
  "wall_s": 99.5,
  "collision": null
}
```

### E2 CF suite_r2_v4_F0_002 imagination_strict look2_T2_A1b summary原文

原运行 `outputs/r3/v3/counterfactuals/suite_r2_v4_F0_002/imagination_strict/look2_T2_A1b/trusted`；exit0，干预及前缀验证pass。

```json
{
  "policy": "imagination_strict",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "stuck",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F0_002",
  "goal": [
    10.301463,
    -0.045753
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 53.32,
  "sensor_mode": "live",
  "looks": 2,
  "final_pose": [
    4.276,
    0.398,
    -1.17
  ],
  "sim_time_s": 54.52,
  "wall_s": 103.5,
  "collision": null
}
```

### E2 CF suite_r2_v4_F0_002 imagination_strict look2_T2_A2b summary原文

原运行 `outputs/r3/v3/counterfactuals/suite_r2_v4_F0_002/imagination_strict/look2_T2_A2b/trusted`；exit0，干预及前缀验证pass。

```json
{
  "policy": "imagination_strict",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "stuck",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F0_002",
  "goal": [
    10.301463,
    -0.045753
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 53.32,
  "sensor_mode": "live",
  "looks": 2,
  "final_pose": [
    4.276,
    0.398,
    -1.17
  ],
  "sim_time_s": 54.52,
  "wall_s": 100.3,
  "collision": null
}
```

### E2 CF suite_r2_v4_F0_002 imagination_strict look2_T2_B1b summary原文

原运行 `outputs/r3/v3/counterfactuals/suite_r2_v4_F0_002/imagination_strict/look2_T2_B1b/trusted`；exit0，干预及前缀验证pass。

```json
{
  "policy": "imagination_strict",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "stuck",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F0_002",
  "goal": [
    10.301463,
    -0.045753
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 53.32,
  "sensor_mode": "live",
  "looks": 2,
  "final_pose": [
    4.276,
    0.398,
    -1.17
  ],
  "sim_time_s": 54.52,
  "wall_s": 100.4,
  "collision": null
}
```

### E2 CF suite_r2_v4_F0_002 imagination_strict look2_T2_C1b summary原文

原运行 `outputs/r3/v3/counterfactuals/suite_r2_v4_F0_002/imagination_strict/look2_T2_C1b/trusted`；exit0，干预及前缀验证pass。

```json
{
  "policy": "imagination_strict",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "stuck",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F0_002",
  "goal": [
    10.301463,
    -0.045753
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 53.32,
  "sensor_mode": "live",
  "looks": 2,
  "final_pose": [
    4.276,
    0.398,
    -1.17
  ],
  "sim_time_s": 54.52,
  "wall_s": 93.3,
  "collision": null
}
```

### E2 CF suite_r2_v4_F0_002 imagination_strict look2_T2_C2b summary原文

原运行 `outputs/r3/v3/counterfactuals/suite_r2_v4_F0_002/imagination_strict/look2_T2_C2b/trusted`；exit0，干预及前缀验证pass。

```json
{
  "policy": "imagination_strict",
  "tag": "trusted",
  "see_dark": false,
  "imagine": "lux",
  "result": "stuck",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F0_002",
  "goal": [
    10.301463,
    -0.045753
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 53.32,
  "sensor_mode": "live",
  "looks": 2,
  "final_pose": [
    4.276,
    0.398,
    -1.17
  ],
  "sim_time_s": 54.52,
  "wall_s": 103.2,
  "collision": null
}
```

F0_002完整保全与核验实际完成：7230files、完整tar432468208bytes、唯一公开scene集100636541bytes（≤150MB）；372去重public对象原SHA与tar全部成员SHA/size均通过。21个成功生成模型及其生成目录所有文件都进入完整清单，raw原件保留在outputs/assets并只在本机Git exclude。证据 [F0-002-custody-audit.json](../../evidence/reviews/beforestep_r3/final-verification/F0-002-custody-audit.json)、[生成资产核验](../../evidence/reviews/beforestep_r3/final-verification/F0-002-generated-assets.json)、[唯一manifest](../../evidence/reviews/beforestep_r3/scenes/suite_r2_v4_F0_002/manifest.json)。

### E2 suite_r2_v4_F3_005 conservative summary原文

固定第三场四baseline提前计算完成，exit0；真实双方法仍按既定顺序在F2之后进入，不按这些结果筛选。

```json
{
  "policy": "conservative",
  "tag": "conservative",
  "see_dark": false,
  "imagine": null,
  "result": "stuck",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F3_005",
  "goal": [
    11.330212,
    0.045812
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 94.18,
  "sensor_mode": "live",
  "looks": 5,
  "final_pose": [
    4.26,
    1.993,
    28.16
  ],
  "sim_time_s": 95.38,
  "wall_s": 55.3,
  "collision": null
}
```

### E2 suite_r2_v4_F3_005 see_dark summary原文

固定第三场四baseline提前计算完成，exit0；真实双方法仍按既定顺序在F2之后进入，不按这些结果筛选。

```json
{
  "policy": "conservative",
  "tag": "see_dark",
  "see_dark": true,
  "imagine": null,
  "result": "arrived",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F3_005",
  "goal": [
    11.330212,
    0.045812
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 137.98,
  "sensor_mode": "live",
  "looks": 3,
  "final_pose": [
    11.323,
    0.046,
    5.63
  ],
  "sim_time_s": 139.18,
  "wall_s": 53.6,
  "collision": null
}
```

### E2 suite_r2_v4_F3_005 optimistic summary原文

固定第三场四baseline提前计算完成，exit0；真实双方法仍按既定顺序在F2之后进入，不按这些结果筛选。

```json
{
  "policy": "optimistic",
  "tag": "optimistic",
  "see_dark": false,
  "imagine": null,
  "result": "collision",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F3_005",
  "goal": [
    11.330212,
    0.045812
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 81.14,
  "sensor_mode": "live",
  "looks": 1,
  "final_pose": [
    6.826,
    -0.62,
    8.13
  ],
  "sim_time_s": 82.34,
  "wall_s": 33.6,
  "collision": {
    "body": "obstacle1",
    "robot_geom": null,
    "pos": [
      7.061,
      -0.368,
      0.119
    ],
    "t": 82.338
  }
}
```

### E2 suite_r2_v4_F3_005 truth summary原文

固定第三场四baseline提前计算完成，exit0；真实双方法仍按既定顺序在F2之后进入，不按这些结果筛选。

```json
{
  "policy": "imagination",
  "tag": "truth",
  "see_dark": false,
  "imagine": "truth",
  "result": "arrived",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F3_005",
  "goal": [
    11.330212,
    0.045812
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 119.52,
  "sensor_mode": "live",
  "looks": 1,
  "final_pose": [
    11.322,
    0.045,
    17.0
  ],
  "sim_time_s": 120.72,
  "wall_s": 55.2,
  "collision": null
}
```

F0_002 publicscene已5735eeb push；368新增LFS96981747bytes已从origin独立storage实际下载，全部Git pointer SHA/size通过。[远端核验](../../evidence/reviews/beforestep_r3/final-verification/F0-002-publication-audit.json)。完整F0实验/新CF/XY/3D/原GLB/失败与输入清单均完成保全，后续监督复用；当前F2真实链继续，不以此阶段结束R3。

### E2 suite_r2_v4_F2_011 imagination summary原文

原方法exit0，第二眼两批12任务中10成功模型仍0准入，依规则停车；无碰撞。未新增第三批。首眼5准入/第二眼0并未保证可通行，strict首眼复用继续。

```json
{
  "policy": "imagination",
  "tag": "imagination",
  "see_dark": false,
  "imagine": "lux",
  "result": "stuck",
  "controller": "rules",
  "controller_sha256": null,
  "pose_controller_sha256": null,
  "scene_id": "suite_r2_v4_F2_011",
  "goal": [
    10.564532,
    -0.007639
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 54.86,
  "sensor_mode": "live",
  "looks": 2,
  "final_pose": [
    4.276,
    0.597,
    -1.72
  ],
  "sim_time_s": 56.06,
  "wall_s": 1028.1,
  "collision": null
}
```

### E2 suite_r2_v4_F2_011 imagination_strict summary原文

strict与原方法均2眼56.06s停车、0碰撞；first5原观测字节复用pass。后眼已知SDK同身份复用，未重create，实际未到达。

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
  "scene_id": "suite_r2_v4_F2_011",
  "goal": [
    10.564532,
    -0.007639
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 54.86,
  "sensor_mode": "live",
  "looks": 2,
  "final_pose": [
    4.276,
    0.597,
    -1.72
  ],
  "sim_time_s": 56.06,
  "wall_s": 134.5,
  "collision": null
}
```

F2_011六栏实际complete；下一固定F3_005已复用提前完成四baseline并进入原想象首眼真实生成。F2原方法新拒CF进行中，已出现强制采纳被拒候选后的碰撞，属于反事实干预结果；真实orig/strict本场均无碰撞。全部17份仍继续，不挑选碰撞样本。
