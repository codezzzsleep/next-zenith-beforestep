# RESULT_BEFORESTEP_R3

执行规格：[SPEC_BEFORESTEP_R3.md](SPEC_BEFORESTEP_R3.md)。R1/R2预注册结果仍为主结果；全部新增方法和实验标为赛后修订。

| 小项 | 内容 | 状态 | 提交/证据 |
| --- | --- | --- | --- |
| P0.1 | 首页/报告顺序与失败分析 | 进行中 | — |
| P0.2 | 全部准入候选背面误差统计/数字核验 | 进行中 | — |
| V0 | 指定原运行的全部公开视频数据索引 | 进行中 | — |
| P0.3 | 本地/公网验收与PDF/Pages | 未开始 | — |
| S1 | imagination_strict与预测阴影 | 未开始 | — |
| S2 | 单测/太阳诊断/全部R1回归/两个替身 | 未开始 | — |
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
