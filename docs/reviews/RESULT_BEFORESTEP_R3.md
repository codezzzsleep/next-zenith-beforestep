# RESULT_BEFORESTEP_R3

执行规格：[SPEC_BEFORESTEP_R3.md](SPEC_BEFORESTEP_R3.md)。R1/R2预注册结果仍为主结果；全部新增方法和实验标为赛后修订。

| 小项 | 内容 | 状态 | 提交/证据 |
| --- | --- | --- | --- |
| P0.1 | 首页/报告顺序与失败分析 | 完成 | c4b18f3；Pages e08f20d/public browser0 |
| P0.2 | 全部准入候选背面误差统计/数字核验 | 完成 | c4b18f3；Pages e08f20d/public browser0 |
| V0 | 指定原运行的全部公开视频数据索引 | 完成 | c4b18f3；Pages e08f20d/public browser0 |
| P0.3 | 本地/公网验收与PDF/Pages | 完成 | c4b18f3；Pages e08f20d/public browser0 |
| S1 | imagination_strict与预测阴影 | 进行中 | 独立strict_pipeline；原pipeline.py未改，72项单测通过 |
| S2 | 单测/太阳诊断/全部R1回归/两个替身 | 进行中 | outputs/qa/r3/S2；现有作业继续，不重开 |
| E1 | 原12冻结场景赛后修订复测 | 未开始 | — |
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
