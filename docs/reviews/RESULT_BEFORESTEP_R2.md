# RESULT_BEFORESTEP_R2

执行规格：[SPEC_BEFORESTEP_R2.md](SPEC_BEFORESTEP_R2.md)。R1仍有效，R2只扩展B/C/D范围。

| 小项 | 内容 | 进度 | 提交 |
| --- | --- | --- | --- |
| A1 | 重验单测、资产SHA、链接、R1数字 | 完成 | 800ef64；发布回执见本提交 |
| A2 | 修重复status并本地浏览器验收 | 完成 | 800ef64；发布回执见本提交 |
| A3 | R1五条结论审计 | 完成 | 800ef64；发布回执见本提交 |
| A4 | R1报告PDF | 完成 | 800ef64；发布回执见本提交 |
| A5 | main/Pages发布及公网验收 | 完成 | 800ef64；发布回执见本提交 |
| A6 | R1结果收尾 | 完成 | 800ef64；发布回执见本提交 |
| B1 | 地形/太阳配置与完整回归 | 完成 | cfffaf8；67测试、完整五R1回归同原 |
| B2 | 参数预注册、生成器、候选池分类 | 完成 | v4主池与F1唯一扩展60场景/240非Lux全完成；名单a810e14 |
| B3 | 冻结场景组并推送 | 完成 | a810e14；远端同SHA |
| B4 | 四类真实形状替身完整链 | 完成 | 当前源cfffaf8四类全链/复盘/allpanes通过；本提交 |
| B5 | 场景组真实Lux3D | 进行中 | B4已push c465926后启动；实时预算见ledger |
| B6 | 全部场景复盘和全部拒绝反事实 | 进行中（复盘随B5，CF父等待已完成场景） | b790e92 |
| B7 | 完整总表 | 未开始 | — |
| B8 | 预定规则结论 | 未开始 | — |
| C1 | 五步关卡模式 | 进行中（R1锚点框架已验证，完整场景组待B完成） | c5be2c6 |
| C2 | 沙盒与一致性 | 进行中（锚点1/1与本地浏览器通过，全组待B） | 本次基础提交 |
| C3 | 导出与人工场景 | 进行中（导出JSON实际验证，人工场景当前无文件） | 本次基础提交 |
| D1 | 首页/报告/相关工作整合 | 未开始 | — |
| D2 | 全验收和main/Pages发布 | 未开始 | — |

## 当前身份与授权

- 开始：2026-11-10 13:51 UTC；main本地/远端均 `40044b46a060ea6862545502c9f0639aff316225`。实际工作区与规格§1吻合：R1网页/报告半成品未提交，src无改动，无实验作业。
- 12个R1真实任务全部終态，沿用原证据，不重新创建。R2新增付费任务：0；累计0/360。
- 单一执行会话核验：进程/root/3d当前终端为本会话，其余codex终端在/root/dshcli；无第二个本项目执行作业。
- 保持四份场景原字节、机器人/传感器链、admission/protocol与规则控制器；新范围按规格预注册，结果好坏全部保留。

## 阶段 A

### A1 运行前预期

全部单测40项、资产323项SHA、文档链接、R1数字核对均应通过，确认旧记录。原失败日志保留，新日志在 `outputs/qa/r2/A1/`。此阶段不改src、不调用Lux3D。

A1实际：`PYTHONPATH=/tmp/lunar-review-20261109-deps:/tmp/beforestep-browser-deps:src python3 -m unittest discover -s tests -v` exit0，40/40（2.122s）；资产323/323 SHA通过；`python3 ops/check_document_links.py` exit0，16文档/139链接无缺失；同PYTHONPATH执行`python3 ops/verify_r1_presentation.py` exit0，9运行、11候选、12预演轨迹与报告HTML及数字来源通过。日志/JSON：`outputs/qa/r2/A1/`。资产审计首调用误用assets键exit1，修为entries键通过；归档数字核对首调用缺PYTHONPATH导致markdown导入失败exit1，恢复相同依赖路径后通过（corrected日志），未修改证据或src。规格提交0a595b5已推送，远端同SHA。

### A2 运行前预期与修正

旧失败中第二个status来自model-viewer的Shadow DOM辅助状态。正文回放状态改唯一`run-status`，同步JS与验收定位，不改src。预期9运行、11GLB、12画廊、三历史场景、20训练回放、390px无溢出且无HTTP/页面错误；通过后生成PDF并再次核对所有结论。

A2首次新验收exit1（`outputs/qa/r2/A2-local-browser.log`）：status定位已通过，时间断言把Python整数浮点104.0与浏览器104字符串比较；改为解析秒数并按原summary精确数值比较，保留初失败，不改展示数值或实验。

A2第二次新验收exit1（corrected日志）：9运行及11GLB均已走到链接核验；Playwright穿透三维库Shadow DOM抓到内部javascript链接，HTTP探测因此报协议错误。链接改为首页light DOM中用户实际链接，仍全部HTTP检查，未删正文链接。

A2最终exit0：`python3 ops/check_r1_browser.py --name r2-A2-local-final --pdf`（相同PYTHONPATH），全部9运行、11真实GLB、12预演画廊、3个历史场景、20学习回放通过；正文状态唯一，390px无横向溢出，图片加载，页面与HTTP错误均0。结果：`evidence/reviews/beforestep_r1/presentation/local-browser.json`；截图留`outputs/qa/r1/r2-A2-local-final-{desktop,mobile,report-mobile}.png`。

A3 `python3 ops/verify_r1_presentation.py` exit0，首页/报告五项口径保持：0/3碰撞与偏保守、47.541mm和XY0、真实一眼与第二眼/6b/B替换未触发、B251px/native_ok=false仍两准入、1223.6s含冷配准/预演不含云排队非端到端、旧gate/改终点/训练为未证必要性的附录。数字结果公开在presentation/numbers.json。

A4通过同一真实Chromium打印报告到`site/media/report.pdf`（1.6MB，未渲染视频），原v0.3 PDF保持在`site/media/history/trained_gate_v03/report.pdf`。PDF读取补验见后文。

A5进行中：main准备提交全部R1网页/报告；Pages导出保留所有当前与历史入口引用的GLB，未引用重复网格只从导出剔除，main资产不变。导出246MB/1160文件，完整数据仍在main。实际配额API只读查询404，凭证缺user scope；本阶段无新增LFS对象（site新增为图片/PDF），不扩权限、不把配额可见性当停工。B入库将按§2.5采取保守精简集+外部完整tar，先检查可用性。

A1–A4与R1正文提交`800ef64`，`git push origin main` exit0，远端main同SHA。A4补验Python pypdf读取5页/1625235bytes，关键结论全部在PDF，SHA ae4ceacbc684b4a681cacee2f19442d80fb3f096e70666e5865a0f4574fb5f87。旧系统未安装pdfinfo/pdftotext，首次调用exit127，改用仅本机临时依赖pypdf补验通过，未改项目运行依赖。Pages提交`49eddf8d51893aca091a4d1ff0f07133c870e3e6`推送exit0，构建中；真实公网验收待构建完成。`git diff --name-only src config`为空。

### 阶段 A 小结（§8格式）

1. 完成并验证：规格/进度0a595b5、网页/报告/本地验收800ef64860566241af11b3f312c848f533b82bc9，远端main同800ef64；Pages49eddf8d51893aca091a4d1ff0f07133c870e3e6构建built/error=null，Actions42829258154 success。`python3 ops/check_r1_browser.py --url https://codezzzsleep.github.io/next-zenith-beforestep/ --name r2-A5-public` exit0，9回放、11GLB、12画廊、3历史场景、20训练回放、390px及全部图片/链接通过，HTTP/页面0错误；公网PDF/视频/数据SHA与本地相同。全部40单测、323资产SHA、139链接和数字审计exit0，PDF5页关键结论补验通过。日志`outputs/qa/r2/A1/`、`A2-local-browser-final.log`、`A5-public-browser.log`；公开摘要`evidence/reviews/beforestep_r1/presentation/`。
2. 做了未验证：无阶段A项遗留。
3. 未完成或失败：初status、时间字符串、Shadow DOM链接与依赖调用失败均已修正；初日志保留。新Demo由负责人制作，保留位置/历史视频，不是本轮自渲染待办。
4. 自决：正文状态独立id；网页只检查light DOM用户链接；时间按summary数值比较；历史资产保留；源码/config零改动。三个时间关口尚未到，不提前收缩。
5. 新增Lux3D任务0，R2累计0/360，旧12个任务不重复创建。
6. 提交前仅本回执改动；无实验/生成作业，本地HTTP8081为验收服务，非实验。
7. 下一第一个动作：B1实现可选terrain/sun配置（缺省完全复现旧值），补单测并跑stress_v8四基线与R1全数组复用回归。

## 阶段 B

### B1 实施前决策与运行预期

可选格式：terrain.type=`corridor|plain`，terrain.craters为`{center:[x,y],radius,depth}`列表，terrain.right_wall布尔；sun.elevation_deg/azimuth_deg。缺省为旧窄道、无坑、有右石堆、10°/35°，四份旧配置原字节保留。月坑为轨道已知禁行区，物理高度场下凹，prior_nogo包含坑沿5cm，车不下坑。旧stress_v8按名字关闭参照预演的历史分支需保留旧效果，改为配置性选项并记录缺省兼容理由，不改变执行预演。地形可视缓存按地形参数SHA隔离，旧默认仍原缓存名保证渲染字节一致。

新实验前预期：stress_v8保守stuck、see_dark arrived、乐观collision、truth arrived；R1 reuse全部t/qpos/phase/actions/sources数组完全相同；全部单测通过。不符合先修，不带不一致进入B2。

B1首次单测47项46通过/1错误，exit1（`outputs/qa/r2/B1-regression/tests.log`）：旧保全清单没有scene高度场文件，测试误用公开不存在的路径，未进入任何物理回归/新实验。从R1原运行完整输出复制257×257原高度场为压缩测试fixture，带原run_id/源提交/数组SHA和NPZ SHA；测试改用此独立冻结数据。旧失败保留，新回归独立目录B1-regression-corrected。

按名字分支审计：pipeline的stress_v8条件已移成REHEARSE_REFERENCE配置；configure只保留缺省历史兼容映射（stress关闭额外参照预演，其余三旧场景开启），因为旧文件不准改且需要原结果/轨迹不变。新池显式设置rehearse_reference=false统一R1流程；这只控制附加参照路线诊断，不控制选路或执行预演。

B1纠正后47/47单测exit0/2.258s；5项物理回归普通计算作业已经开始，父session96685、`outputs/qa/r2/B1-regression-corrected/regression.json`记录源SHA/6冻结文件SHA/每项完成回执，日志同目录。未通过完整回归前不运行新场景、不调用Lux。

### B1 验证完成与B2启动前预注册

`python3 ops/run_r2_regression.py --out outputs/qa/r2/B1-regression-corrected --workers 3` exit0：六份冻结文件SHA不变，全部五回归通过。四非Lux结果/眼数/仿真时间与R1一致；reuse到达、12/12预演完成无碰撞，全部t/qpos/phase/actions/sources数组逐项相同，traj.npz SHA同原。首次47测试fixture路径错误已修正，新全部52/52 exit0/2.436s（含生成器/分类契约）。公开证据`evidence/suite/regressions/B1/`，原始全部回归运行保留在outputs/qa/r2/B1-regression-corrected。

其余源码命名审计：scene/pipeline场景默认值为兼容入口，场景组显式传入新配置；delivery/artifacts.py的旧两场景列表和回退属于旧交付/视频生成器，本轮不调用且用于历史保留，故保留，场景组用新的ops生成数据，不用旧build覆盖主展示。不修改传感器链/冻门槛/机器人。

五项summary.json原文：

#### B1/conservative

命令与exit0见公开regression.json。

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
  "wall_s": 121.0,
  "collision": null
}
```

#### B1/see_dark

命令与exit0见公开regression.json。

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
  "scene_id": "stress_v8",
  "goal": [
    10.5,
    0.0
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 146.06,
  "sensor_mode": "live",
  "looks": 3,
  "final_pose": [
    10.491,
    -0.001,
    18.08
  ],
  "sim_time_s": 147.26,
  "wall_s": 114.7,
  "collision": null
}
```

#### B1/optimistic

命令与exit0见公开regression.json。

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
  "scene_id": "stress_v8",
  "goal": [
    10.5,
    0.0
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 79.67,
  "sensor_mode": "live",
  "looks": 1,
  "final_pose": [
    6.713,
    -0.526,
    7.58
  ],
  "sim_time_s": 80.87,
  "wall_s": 74.0,
  "collision": {
    "body": "obstacle1",
    "robot_geom": null,
    "pos": [
      6.954,
      -0.276,
      0.111
    ],
    "t": 80.866
  }
}
```

#### B1/truth

命令与exit0见公开regression.json。

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
  "scene_id": "stress_v8",
  "goal": [
    10.5,
    0.0
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 114.68,
  "sensor_mode": "live",
  "looks": 1,
  "final_pose": [
    10.492,
    -0.001,
    19.09
  ],
  "sim_time_s": 115.88,
  "wall_s": 82.5,
  "collision": null
}
```

#### B1/replay

命令与exit0见公开regression.json。

```json
{
  "policy": "imagination",
  "tag": "replay",
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
  "execution_elapsed_s": 111.64,
  "sensor_mode": "live",
  "looks": 1,
  "final_pose": [
    10.492,
    -0.001,
    10.57
  ],
  "sim_time_s": 112.84,
  "wall_s": 434.7,
  "collision": null
}
```

B2首次池运行预期：每类12个种子，共48场景/192次非Lux运行；不预设分类比例，不调Lux。只按四结果用原规则分类，全部输出保留；目标每类2决定性/1普通，不足时按原规则扩一次13–24。参数、随机数规则、岩石/布局/太阳/月坑范围已在docs/decisions.md写明，并在本次提交推送后才生成/运行。禁止单场景修改。

运行命令预注册：`python3 ops/generate_suite_pool.py --params config/suite/pool_v1.json`；随后`python3 ops/run_suite_pool.py --manifest evidence/suite/pool/r2_v1/manifest_F0_F1_F2_F3_1_12.json --out outputs/suite/pool/r2_v1 --regression evidence/suite/regressions/B1/regression.json --workers 3`。退出预期0，分类/到达/碰撞原样报告，不把执行错误当无解。R2新付费仍0/360。

B2运行中发现全局复现错误（不是按结果调参）：`rock_asset_uniform()`以int(height×1000)命名缓存。池F3/009与F2/010同岩石分别0.594954/0.594908m，共享缓存名，先运行的形状会影响后运行的物理输入；此外新缓存非原子写有并发风险。修复仅新配置启用精确高度缓存身份，旧四场景默认旧缓存原字节不变，写入改原子替换。保留首池全部已完成/部分输出作为中断错误记录；停止其普通进程避免源混用，完整§2.2回归后将全部48场景四运行重跑，不挑单例、不调Lux。生成器数值范围/种子不改，新revision仅记录缓存选项。

B6前置源码兼容：现有--trust固定在首眼干预，不能逐一运行真实第二眼的拒绝候选。新增仅反事实启用的--trust-look=2：首眼及去观察点的前缀按原准入/预演/控制完整重放，第二眼按该眼目标编号强制单候选，之后不补看；原--trust默认首眼不变。新增干预事件记录实际来源眼数/候选，避免未来观测泄露到首眼和未干预却计为成功。该必要支持在任何场景组Lux之前实现，随后再完整§2.2回归；不改变主线或场景组生产传感器/门槛/两眼/rules。

B1精确缓存版本完整五回归已通过（父21524完成，outputs/qa/r2/B1-exact-cache-regression/，53tests、全部5结果与R1重放5数组相同）。随后必要的第二眼反事实入口使最终源身份变化，因此正在独立B1-final-suite-regression再验证，父79642/workers2；原版本source_variants与全部输出保留，不冒充最新源码已通过。最终回归启动时57单测通过；付费预算mock测试证明先持久预留再create、360硬上限、uncertain只query、确定未提交释放容量而保留身份历史，未产生真实任务。

B2第一池源/参数96fa0b7、48候选提交9be060a；普通父18431被主动终止exit143以修全局缓存，原pool.json/每项command/process/log/已完成及partial数据全部保留，不能纳入最终冻结组。第二池pool_v2范围、种子/RNG不变，精确缓存选项全池启用；最终源完整回归及提交推送后才生成/运行。

最终B1/source含缓存和CF入口：`python3 ops/run_r2_regression.py --out outputs/qa/r2/B1-final-suite-regression --workers 2` exit0，57/57单测通过，6份冻结文件SHA不变，4非Lux结果/眼数/时间同R1，reuse到达/12预演全完成无碰撞，5轨迹数组与NPZ SHA全同。公开evidence/suite/regressions/B1-final。修复未改旧物理场景、门槛、两眼、传感器或控制，源/参数/预算与全链驱动在本次推送后才启动第二池。

B2第二池命令预注册：`python3 ops/generate_suite_pool.py --params config/suite/pool_v2.json`，全部48场景；`python3 ops/run_suite_pool.py --manifest evidence/suite/pool/r2_v2/manifest_F0_F1_F2_F3_1_12.json --out outputs/suite/pool/r2_v2 --regression evidence/suite/regressions/B1-final/regression.json --workers 3`。预期192项非Luxexit0，按既定分类，数据好坏全保留。池期间补测`ops/check_second_look_counterfactual.py`：R1离线两眼替身作为机制验证，第二眼前全部轨迹数组同原，干预仅look2，0付费；不纳入场景组实测。

第二眼CF完整离线机制验证exit0：`python3 ops/check_second_look_counterfactual.py --regression evidence/suite/regressions/B1-final/regression.json --out outputs/qa/r2/look2-counterfactual`。137.2s/2眼到达，无碰撞；唯一干预在look2/T2/A1，second-look前t/qpos/phase/control_actions/control_sources全部逐项同原，实际第二眼pose/time相同。素材是R1真实形状离线替身，0付费，不证明真实Lux第二眼或自检防撞。小证据evidence/suite/regressions/look2-counterfactual/validation.json，完整输出outputs/qa/r2/look2-counterfactual。

最终源码4f554c7与第二池48配置b956530均已推main；v2pool已启动192非Lux，父session45403，权威pool.json随完成原子写。当前首个F0/001四运行全部exit0（保守stuck、see-dark arrived、乐观arrived、truth arrived），按规则为普通，尚不冻结任何名单；R2新增付费0/360。

B2第二池192项已全结束（父45403 exit1，执行错误保留）：F0=0决定性/10普通/2无解；F1=12执行错误（平坦可视mesh零体积，不能当无解）；F2=0决定性/7普通/4无解/1执行错误；F3=1决定性/6普通/5无解。全部原summary、命令、run_id、stdout在outputs/suite/pool/r2_v2，汇总原文evidence/suite/pool/r2_v2/manifest_F0_F1_F2_F3_1_12_results.json。尚未冻组选取、未调Lux。

两个实际程序错误：F1所有图像创建时v8_ground平坦mesh体积0被MuJoCo拒绝；F2/004 see-dark在need_mask空时centroid为NaN标量导致IndexError。另对候选点越地图边界加入索引保护。只改新平地可视mesh编译的shell惯量（不增地形厚度、不改相机/传感器参数）、空ROI返回无候选、越界跳过，旧所有有候选情况排序不变。最小零体积面片的shell属性已实际编译验证。旧池全部完成后才改源，避免混用源码。改完再完整§2.2回归、单测；重新生成全池，在非Lux分类基础上按规则扩不足2决定性的类别13–24一次，所有旧池保留。

数据保全脚本先实际验证于已完成F0/001：96文件、46.26MB精简公有对象、46.53MB完整外部tar，单场景远低于150MB；原字节SHA与gzip恢复均验证。完整tar在/root/3d/artifacts/beforestep-r2，未包含凭证或上传账本。单测59/59通过（含按种子最早选择与禁止普通替代决定性）；ops/freeze_suite.py仅写好了，不实际冻结。

B1此次修复新增3测试全部实际通过，当前62/62（2.430s）：真实零厚度平面mesh以shell惯量编译且重建z坐标仍0；空unknown需求返回无观察候选；临近地图尾端的全部候选索引合法；旧黄金排序与冻结fixture仍通过。当前完整五物理回归正在收尾，source发生变化后尚不运行新场景。

B2 v3预注册：pool_v3仅改revision，所有参数范围、种子/RNG同v2。F0/F2/F3依据D0/D0/D1各扩13–24一次，并用修复后源码重新跑1–24；F2一个错误即便修复成决定性也最多1，仍不足2。F1先用修复源跑1–12，原12全部编译失败，不能据错误判断分类不足。合计本轮先84候选/336非Lux运行；F1完整结果不足2再扩13–24一次。旧所有结果保留，0新Lux。全回归通过并提交源后才生成v3配置并开跑。

B1平地/空需求/边界修复后完整5回归exit0：`python3 ops/run_r2_regression.py --out outputs/qa/r2/B1-flat-and-view-regression --workers 3`，62tests全部通过，6冻结文件SHA不变，四基线结果与眼数/时间同R1，reuse12预演全pass、5数组与NPZ SHA同原。证据evidence/suite/regressions/B1-flat-and-view。源/参数提交推送后才能v3生成并运行；B6全拒绝反事实与3D/XY复盘驱动写好了，只py_compile，实际场景组验证尚未开始。

合并池命令预注册：分别`generate_suite_pool.py --params config/suite/pool_v3.json --family F0 F2 F3 --seeds 1 24`与`--family F1 --seeds 1 12`，合并为一个84场景manifest，并提交全部生成配置；`run_suite_pool.py --manifest evidence/suite/pool/r2_v3/manifest_initial_and_expansion.json --out outputs/suite/pool/r2_v3 --regression evidence/suite/regressions/B1-flat-and-view/regression.json --workers 3`，先336非Lux，零新付费。

## C1 独立框架工作（B2池等待期间）

五步关卡已接真实R1 stress锚点：首眼只显示实际RGB与两类未知/已知禁行地图；选择后三种实际轨迹可回放；揭晓才画真值与全部准入/拒绝占地；3D注册候选与真实扫描同坐标同单位切换；首次选择只计一次，对比三种固定策略已经玩的通过数。没有伪造第二个场景或结果，开发payload明确anchor_only_development。主首页/Pages仍R1，待B全部真实结果完成后接入完整场景组并按D发布。

`python3 ops/build_levels_site.py --anchor-only` exit0，1真实关/11原候选的注册网格与2真实扫描；`node --input-type=module --check < site/levels.js` exit0；`python3 ops/check_levels_browser.py --name C1-anchor-final` exit0，五步、3实际策略回放、11候选与真实mesh切换/旋转、首次选择计分、390px无溢出、HTTP/页面错误0。手机版实际model进入视口后截图已看见网格。第一版变量g重复导致JS parse失败，原日志C1-anchor-browser.log保留，已修且最终验收通过；中间全页截图远离model时lazy render空白，最终滚入视口验证实际渲染。公开小回执evidence/suite/presentation/anchor-game/browser.json，截图/日志outputs/qa/r2/C1-anchor-final-*。

做了未实际验证：B4全链验收汇总、B7原始数据总表/B8结论脚本（只py_compile）。没有完成B3冻结/B4四类替身/B5真实Lux/B6全部真实反事实/B7全组/C2C3/D。仍0/360。

## C2/C3 基础验证与归档可恢复性（B2池期间）

只使用R1真实锚点进行开发验证，尚未完成整组C2，未发布新Pages。12种真实扫描占地、同扫描岩石全部准入候选占地模板、真实5cm格子、转向节点/直线边、0.40m行驶半径/0.57m转向半径和5cm想象膨胀已接入。未知无准入模板按附近未知保留。俯视几何影子明确为近似，不冒充RGB-D或物理模拟；原样载入场景也用该独立近似，不偷换成保存的首眼地图来凑一致。

`python3 ops/build_sandbox_data.py` exit0，12扫描/1锚点/2扫描有实际准入模板；`python3 ops/check_sandbox_browser.py --name C2-anchor` exit0，实际拖动、旋转45°、高度0.45、加坑/删除、太阳50°、三策略出路线、导出JSON字节内容验证，390px无溢出，HTTP/页面0错误。截图已人工查看。`python3 ops/check_sandbox_consistency.py` exit0，锚点三策略定性1/1一致（乐观有路/XY侵入，保守无路，想象有路/XY侵入；最后一项不等于3D碰撞，和R1复盘相容）；精确保存地图的EDT最大误差0、规划有路性相同，单独报告，不充作编辑器一致性数字。日志outputs/qa/r2/C2-anchor-{browser,consistency}.log；公开小证据evidence/suite/presentation/sandbox-anchor。

`preserve_suite_scene.py`增加GitHub可直接查看的summary/run_identity/eval，避免B7链接指向未入库outputs；`restore_suite_scene.py`实际验证完整外部tar内96原文件的SHA/size且0覆盖（已有相同原数据），日志preservation-v2[-restore].log，精简46,293,324bytes/完整46,526,777bytes，均不另公推该非最终场景大数据。docs/sandbox.md含不付费真值/完整替身、本人密钥真实调用、身份恢复和证据恢复步骤。文档17项146链接通过，R1数字审计仍exit0；src无diff。

B7表/原因、整合首页报告、扩展原数字核验已写脚本，只有py_compile与R1不回退审计，完整suite验证待B。不把脚本存在记成结果。现有v3父PID2130778继续3进程，约79/336（易变），新Lux0/360；时间关口未到，无提前收缩、无代理。

### C/D 保管与整合边界

沙盒/归档基础ead1d9e已推main，远端同SHA。后续场景精简SHA对象与关卡配准网格均走LFS（新增patterns），完整原GLB与完整物理数据保留外部tar；每场景仍≤150MB。A阶段已实际尝试查询配额API404且无user scope，不能冒称剩余额度已知；按§2.5保守使用外部完整包，上传前检查新增对象量和实际LFS上传/可用性，失败时继续保留外部完整包并报告。旧main资产和正式发布不删。

D整合脚本保留R1八段与旧报告打印样式，按实际Markdown路径换网页链接；首页关卡以同源嵌入显示，另有完整关卡入口，嵌入按实际内容高度调整，避免移动端截断。脚本只compile，整组数据不存在所以没有提前写首页/报告或冒称发布。

嵌入与保管实际补验：`check_levels_browser.py --name C1-anchor-embed-fix` exit0，全五步/3回放/11候选网格/计分与390px、HTTP/页面0错误；独立390px同源iframe实际收到高度1162px且隐藏内部header、内文无横溢出（C1-embed-validation.json，public anchor-game/embed.json）。沙盒开过区域改为0.42m半径线段胶囊，重跑独立近似首眼1/1一致、精确EDT0。13关卡网格总7.5MB的原字节归一到LFS，SHA不变；仅传输方式变，不改场景/门槛/源。

### B2 F0扩展完成与范围调整预注册

2026-11-10 16:47 UTC，v3 F0所有24×4非Lux已完整终态：0决定性/17普通/7无解，0执行错误；锚点加进来也仅1决定性。F1/F2/F3仍运行，F1前两个完整候选为1决定性/1无解，不拿局部结果冻结。按B2记录F0参数调整，config/suite/pool_v4.json与decisions列出全部范围，旧0/24保留；不修改单个scene，不改stress，不看真实Lux。v4只预注册、未生成/未运行，须等v3全部完成与F1合规扩展判断后整四类别新池（不只跑F0）。可选role高度/类别覆盖的生成器缺省对全部84旧v3配置逐字节相同；当前完整测试预期63，物理src仍671a4e6，因此此前五回归identity不变。

新生成器兼容测试实际63/63 exit0（4.554s，B2-generator-compatibility-tests.log），84既注册v3配置字节完全相同。源SHA清单仍与B1-flat-and-view完整5回归一致；不重复跑未变物理源。B6后处理驱动在复制的真实R1锚点上实测exit0：3D47.541283739641456mm、XY0、乐观原路线压入218.988625657973mm，与原复盘相同；只验证helper，不计新组实测，原R1未覆盖。public evidence/suite/regressions/postmortem-helper/validation.json，原输出outputs/qa/r2/postmortem-helper。新Lux仍0/360。

完整F0分类的原始summary/run_id与尚未完成其他类别的当前进度已同步到evidence/suite/pool/r2_v3/manifest_initial_and_expansion_results.json；completed=false，不可用于冻结。原runner结束后会将同一文件更新为全336终态及最终counts，Git历史保留本次完整F0判断时的非Lux依据。v4预注册d7a1004已推main，远端同SHA。

### B2 F1初始池完成与唯一扩展预期

F1修复后的种子1–12全部48非Luxexit0：D1/O5/U5/未归类1，0执行错误。决定性不足2，按B2追加13–24一次，参数范围/RNG/source不变，不拿see-dark碰撞当执行错误、不放宽分类。现有336池继续跑F2/F3；新增F1扩展单独out outputs/suite/pool/r2_v3_f1_expansion，workers1普通计算，避免重复任何已有任务。当前约3GB/physics进程，可用内存9.1GB（第三进程尚在加载），一额外F1进程预计≤3.2GB；总四普通进程，不使用代理。

生成预期：`generate_suite_pool.py --params config/suite/pool_v3.json --family F1 --seeds 13 24` exit0，12个候选。配置/manifest提交推送之后才运行：`run_suite_pool.py --manifest evidence/suite/pool/r2_v3/manifest_F1_13_24.json --out outputs/suite/pool/r2_v3_f1_expansion --regression evidence/suite/regressions/B1-flat-and-view/regression.json --workers 1`，预期48次exit0并按原定义分类，不预设决定性个数。全部原结果保留；新增Lux0/360。

C2边界补验：模板逆变换查询加入二维索引边界，避免拖出视野的源格子被线性索引折回到另一行；`check_sandbox_consistency.py` exit0，锚点独立近似仍1/1、精确EDT误差0（C2-anchor-grid-bounds.log）。D报告转换将目录证据链接指向GitHub实际目录，避免Pages无目录索引；整合脚本compile，完整D待B。

后续B5付费前，另检查多目标第二眼的全局停止：当前pipeline在某一目标6b仍零准入时设置sampling_exhausted，但只在目标循环之后停车；若同一眼另有零准入目标，prepare_second_batch可能先写额外6b。需要离线验证“已有目标用满12份后停车、仍对已生成GLB完成自检”的请求行为。当前未改src，正在跑的两个池保持源671a4e6；若需修正，等两个池终态后一次改source并跑完整§2.2与全部单测，再进入下一完整新池/B4，0付费阶段允许修，不带不一致前进。

多目标停止专项IO已经复现，预期断言exit1（`outputs/qa/r2/multi-target-stop/before.log`，public regressions/multi-target-stop/before.*）：在模拟的同眼两个目标中，T1原6+6b共12份全部失败/准入0、已有全局sampling_exhausted=true，继续T2的当前prepare_second_batch仍会写另外6份请求。无真实Lux、无物理模拟、0付费；这个失败是新增场景付费之前发现的请求状态缺口。需保持所有已生成GLB自检，在已有一目标用满12份时禁止给剩余目标新增6b；不改阈值/两眼/相机/控制。两个池仍在跑，暂不改src避免混源；待终态后一次修、63+新机制测试和完整§2.2全回归，通过后再新池/B4。

C1真值访问补齐：build_levels_site重建R1锚点exit0，独立真实扫描入口不依赖生成候选；合并观测目标的真实参考为对应扫描组合；候选/真值按原物理场景body世界位置归一（R1 B的body_z=0.00002m）。JS语法通过，当前只构建验证；早启动的浏览器在build未终态前主动停止exit143，原C1-truth-access-browser.log保留；构建后C1-truth-access-final浏览器也返回143，原因未确认、日志空，不冒称通过。待两个候选池结束后再做完整C1浏览器，原c5be2c6五步验收仍保留。

C2扫描库现用与正式场景相同的主轴对齐/底面归零/等比尺度（S.rock_asset_uniform），不再用原扫描任意坐标框。`build_sandbox_data.py`与`check_sandbox_consistency.py`均exit0；12扫描/1锚点/2扫描有准入模板，独立近似仍1/1、精确地图EDT误差0（C2-canonical-scan-*.log）。仅修查看/沙盒数据，src无改动，两个非Lux池仍同source。

### B2 F2扩池完整终态与下一整池注册

v3 F2全部24×4完成exit0：0决定性/16普通/8无解/0执行错误。按B2调整尚未运行的v4参数，F2采用下坑前A/上坑后B、两坑0.65–0.80m、坑沿gap0.15–0.30m、角色高度与太阳/目标的固定随机范围；全部范围与目的见decisions及pool_v4。旧0/24结果完整保留，仍不调Lux、不改单场景。`python3 -m unittest discover -s tests -v` exit0，64/64（7.582s），默认生成器全部84已注册v3配置逐字节相同，新F2角色与坑沿约束通过；日志B2-rim-generator-tests.log。物理src仍同671a4e6，现有F3/F1扩展不受影响。

### B2 F1唯一扩展终态

F1种子13–24的48非Lux全部exit0，父2745203/session39826已完成：D1/O5/U3/未归类3；与初始1–12合计24场景为D2/O10/U8/未归类4，0执行错误。原始所有summary/run_id/命令见evidence/suite/pool/r2_v3/manifest_F1_13_24_results.json与初始results，raw outputs/suite/pool/r2_v3_f1_expansion。达到2D，但不提前冻结：原v3 F3仍运行，下一完整新池需源stop修复/全R1回归/所有候选提交后再跑。F1不调整参数范围，仍保持原广范围。

关卡地图的DARK=2改棕色、HIDDEN=3改紫色，使配色与图例语义一致；JS语法通过，只改查看，不改观测数据/实验结果。

F1扩展工具回执补充：`write_stdin(session39826)`返回工具会话143，不能把它记作driver的实测0。独立parent PID2745203已退出，pool.json的completed=true、全部48子运行记录exit_code=0、最终counts与公开结果均齐全；driver退出码未单独捕获，tool wrapper143保留。按持久结果确认全部48物理变体完成，不重跑或覆盖已完数据。

### B2 v3及唯一F1扩展全部完成

原84场景336子运行全部终态exit0，原parent2130778已退出，pool.json completed=true，最终public manifest_initial_and_expansion_results.json保全。合并F1扩展后96场景/384运行：F0 D0/O17/U7，F1 D2/O10/U8/未归类4，F2 D0/O16/U8，F3 D1/O9/U14；全部0执行错误。工具父会话可能已终止，退出码未单独捕获，记录的所有384物理子运行均0/全部summary齐；不重跑旧结果。

F3扩24仍只有1D，按B2在尚未生成的v4范围加入F3角色尺度和摆放调整，旧1/24/14U不删除：前石rock07 0.53–0.57、后石80%moon04/20%moon02 0.40–0.44，A/B摆放/yaw/太阳为已登记锚点邻域；第三散石height0.35–0.45/x8.0–8.4/y-1.6至1.7，goal10.5–11.5（仍8–12m）；月坑r0.65–0.80/深0.4–0.8、上坑x6.4–7.0/y1.5–1.8、下坑x4.9–5.4/y-1.9至-1.65，一/两坑、2–4石仍不变。目的减少原宽石/近第三石造成的固定流程无解，保持坑与散石混合、不改单一scene。全部范围先写decisions/params并提交；未调任何Lux。

原两父都已结束后才开始修multi-target sampling stop：只阻止已有目标12份零准入之后新写其他6b，仍自检已生成全部候选；默认原R1行为保持。运行前预期：所有单测（含新停止状态IO）、四R1基线同原与R1全数组reuse同原；新gate out outputs/qa/r2/B1-global-stop-regression。过关并push后才生成/运行完整v4新池。

### B1新全局停止实现完整回归通过

`run_r2_regression.py --out outputs/qa/r2/B1-global-stop-regression --workers 3` driver工具退出码0，65/65测试（2.701s），六冻结配置SHA不变；四基线结果/眼数/仿真时间同R1，完整reuse12格预演全pass、traj.npz全部数组逐项相同。所有五子运行exit0，公开regressions/B1-global-stop/{regression.json,tests.log,driver.log}，完整原运行仍outputs。

多目标after IO exit0：第一目标十二份失败/准入0、全局exhausted=true，下一目标不再写6b（额外0份）；原before exit1保留，公开regressions/multi-target-stop/after.*。只修请求创建停止，既有GLB仍走原自检，未改阈值/两眼/控制/相机/传感器。legacy sampling_stop事件中的R1 §2.4文字标记不触发B替换，R2 helper只停车，套组一律不换场景。

C2单位扫描用exact高度缓存创建，避免单位尺寸预处理占用旧legacy毫米缓存键；恢复现场profile，再读取原场景。只改导出helper，不影响上述src回归。下一先提交源/完整结果/F0F2F3所有参数注册并push，再生成v4四类别初始1–12全48配置并push、运行192非Lux；F1若仍不足2按新池实际结果扩13–24一次。0新付费/360。

新版C1补验成功：`check_levels_browser.py --name C1-truth-final-idle` exit0，全五步、3真实回放/11候选/所有独立真实扫描、first-choice计分、无候选真值回退UI fixture、390px和0page/HTTP错误均pass。两次143前日志保留，不再把其当最新验收状态；public anchor-game/browser.json更新，截图/原日志C1-truth-final-idle-*。C2 exact单位扫描build+独立近似一致性仍1/1、精确EDT0，exit0；回归src两文件没有再变，全部五gate仍有效。下一v4首先只1–12每类，按新池结果不足再扩一次13–24，不偷用未来结果。

### B2 v4全部候选已注册，运行前预期

源修正/65测试/五R1gate/参数完整提交7833286已推；v4全部四类别各1–12的48配置与SHA manifest提交28e7302已推（尚非B3最终组）。现在运行`run_suite_pool.py --manifest evidence/suite/pool/r2_v4/manifest_F0_F1_F2_F3_1_12.json --out outputs/suite/pool/r2_v4 --regression evidence/suite/regressions/B1-global-stop/regression.json --workers 3`。预期192个非Lux子运行exit0；分类只按原三类定义，未归类单列，不预设结果或比例。每类不足2D再按新池实际完整12结果判断扩13–24一次，仍不足则B2允许整池改范围。无真实Lux，仍0/360，B3最终freeze未创建。

### B2 v4 F0初始池完整结果

F0种子1–12所有48子运行exit0，D9/O2/U1，0执行错误；原v3宽范围0/24与新邻域9/12并排保留，不能将集中分布比例当成任意月面发生频率。只说明有更多符合D定义的任务，不是实际Lux收益（本轮尚0付费）。其它三类还在跑，当前results completed=false，不可提前B3冻结。完整原summary/identity/命令已同步该v4同一results路径，raw仍outputs/suite/pool/r2_v4。docs/sandbox.md的本地全链示例已指向最新B1-global-stop源回归，避免调用旧源SHA而拒绝。

### B2 v4 F1初始完整结果与唯一扩展

F1所有1–12×4已exit0，D1/O5/U5/未归类1，和同范围旧源结果一致。按B2基于本版实际完整结果不足2，追加13–24一次；参数/源码不变，预期新12×4子运行exit0，分类比例不预设。生成命令`generate_suite_pool.py --params config/suite/pool_v4.json --family F1 --seeds 13 24`，配置/manifest先push，随后新out outputs/suite/pool/r2_v4_f1_expansion、workers1，regression B1-global-stop；当前主池PID1099606保持跑F2/F3，总四普通进程，内存available7GB、新F1预期3GB。无代理，无新Lux，0/360，B3尚未freeze。

### B2 v4 F2初始池完整结果

F2 1–12所有48子运行exit0，D3/O8/未归类1、U0/error0；旧v3宽范围D0/O16/U8（24个）与新预注册范围D3/O8/未归类1（12个）都保留，不把新比例外推为任意月面。F0/F2均已满足2D+至少1O，F1新池扩展仍运行，F3初始仍运行；不能提前冻结最终名单或收费。全部已完成原summary/identity/commands在当前同一v4 results，completed=false。新paid0/360，源7833286不变。

### B2 v4主池全部终态

主pool parent1099606/tool58317实际exit0，48场景192物理子运行全exit0/0error，completed=true：F0 D9/O2/U1；F1初始D1/O5/U5/未归类1；F2 D3/O8/未归类1；F3 D5/O3/U2/未归类2。全部原summary/commands/run_id在最终v4 results及raw outputs。F0/F2/F3已有足够2D/1O，F1扩展仍未全完；B3保持未创建，不能提前收费。

### 阶段B2小结（§8）

1. 完成并验证：v4 48主池/192子运行与F1唯一12扩展/48子运行全部exit0；共60候选/240非Lux，最终F0 D9/O2/U1，F1 D2/O10/U8/未归类4，F2 D3/O8/未归类1，F3 D5/O3/U2/未归类2。65tests/5R1回归在7833286通过，原6config SHA与5轨迹数组同。main prior3bc88da/de6ffc0均已推，原命令/raw logs/summary在各pool目录及公开results。
2. 未验证：实际新组Lux尚未运行；C1/C2只有R1锚点基础，不能当完整组完成。
3. 原失败：v1cache中断、v2flat/emptyROI错误、globalstop IO before失败都保留；已在不降低冻结门槛的条件下修复并回归。
4. 自决：按完整非Lux池不足D调整整池范围，F1按新12实际结果仅一次扩13–24；未改单场景、未看Lux筛选。关口日期尚未到，未提前收缩。
5. 新付费0，累计0/360。
6. 两v4父均已完成，当前无物理/云/训练/视频jobs；提交前仅本冻结/结果改动。
7. 下一具体动作：B3最终名单/预期push，再B4四类最早新D完整standin全链。

## R2 B3 最终场景组冻结

在本轮真实Lux结果之前，仅依据全部四非Lux结果，按每类seed最小取2D与1O；stress_v8作为F0第一个D直接计入。最终12个场景，冻结后不增删替换，不放宽任何门槛。

| 场景 | 类别 | 分类 | 种子 | 保守/see-dark/乐观/真值检验（结果·眼数·仿真s） |
| --- | --- | --- | --- | --- |
| stress_v8 | F0 | decisive | None | stuck·5·142.2 / arrived·3·147.26 / collision·1·80.87 / arrived·1·115.88 |
| suite_r2_v4_F0_001 | F0 | decisive | 1 | stuck·5·142.92 / arrived·3·145.24 / collision·1·80.83 / arrived·1·114.84 |
| suite_r2_v4_F0_005 | F0 | ordinary | 5 | stuck·5·143.98 / arrived·3·151.76 / arrived·1·102.42 / arrived·1·114.6 |
| suite_r2_v4_F1_001 | F1 | decisive | 1 | stuck·5·111.74 / collision·4·91.03 / collision·1·72.47 / arrived·2·124.38 |
| suite_r2_v4_F1_020 | F1 | decisive | 20 | stuck·5·129.12 / stopped_short·4·121.09 / collision·1·79.24 / arrived·1·78.16 |
| suite_r2_v4_F1_003 | F1 | ordinary | 3 | collision·4·134.49 / arrived·5·129.45 / arrived·1·105.18 / arrived·1·99.64 |
| suite_r2_v4_F2_003 | F2 | decisive | 3 | stuck·5·83.06 / arrived·4·165.2 / collision·1·82.79 / arrived·1·124.92 |
| suite_r2_v4_F2_007 | F2 | decisive | 7 | stuck·5·83.33 / arrived·4·157.28 / collision·1·80.41 / arrived·1·112.56 |
| suite_r2_v4_F2_001 | F2 | ordinary | 1 | stuck·5·83.43 / arrived·3·133.18 / arrived·1·102.5 / arrived·1·102.5 |
| suite_r2_v4_F3_002 | F3 | decisive | 2 | stuck·5·218.48 / arrived·5·119.05 / collision·1·80.4 / arrived·1·117.54 |
| suite_r2_v4_F3_004 | F3 | decisive | 4 | stuck·1·18.1 / stopped_short·4·129.63 / collision·1·79.59 / arrived·1·106.44 |
| suite_r2_v4_F3_001 | F3 | ordinary | 1 | stopped_short·2·111.83 / arrived·3·125.97 / arrived·1·111.88 / arrived·1·107.64 |

完整四次summary/命令/退出码/run_id与config SHA见config/suite/frozen.json（SHA256 2c140698a8816b73f0bf1846e921dfb8029268125d08b2e71d26bb48f2f55b75）和两份最终pool results。场景组里stress_v8沿用R1实际真实Lux112.84s/1眼/无碰撞，不再付费或新跑。

每个新场景Lux运行前预期：规则控制器、≤2眼、所有选定路线候选组合的物理预演完整无碰撞、独立执行无碰撞到达；普通场景也预期到达，额外眼数/仿真时间如实测量。若失败、候选全拒或停车，原样报告，不改本名单/门槛/机器人/控制器/太阳。第二眼条件与同输入6b一次严格按原协议，任一目标12仍零准入即安全停车，B替换不用于套组。

B4预期：选择每类本名单中最早的新D（F0_001/F1_001/F2_003/F3_002），以真实扫描资产替身、生产注册/自检/预演/执行全链运行；不调Lux，四类都pass才付费。原失败与任何源修必须先R1完整回归，不挑Lux结果。

B3冻结a810e142a15b37ee1b113b0a0a72eb4ec68c6c27已push exit0且ls-remote同。B4普通dispatcher启动，四类各最早新D/两个并行Python子进程，准确命令/子PID/日志/exit/summary由outputs/suite/standins/b4-processes.json记录，source7833286、regression B1-global-stop。每scene mode=standin/provenance not_real_lux，不付费、不计实际Lux收益。全四结束并all_passed才开始B5。

### B4 替身发现预演地形配置遗漏（付费前）

F0替身2眼到达130.92s、无执行碰撞；复盘命令首次少了optimistic/run目录exit1，正确路径重试exit0（B4-F0_001-review-corrected.log）。F1第一眼预演在(3.354,-1.35)撞obstacle2：真实F1 terrain.right_wall=false，但geometry/imagination.py::rehearsal_spec仍无条件添加旧窄道右墙，导致不存在的物理障碍影响预演。原F1/F3部分输出、F0/F2完整结果、B4-driver与before-wall-fix ledger全部保留于outputs/suite/standins；原dispatcher已停止，停止前F2已完成、F3刚启动的部分输出也保留，不重复此out。

这是B1场景配置覆盖遗漏，按B4许可修程序错误：右墙只在terrain.right_wall=true加入，缺省旧场景不变；不改冻结规则/门槛/机器人/传感器/控制/名单。运行前预期：新增场景预演尊重无墙配置、legacy生成规格仍同；全单测与stress四基线/真实reuse全部数组相同。新独立gate outputs/qa/r2/B1-rehearsal-wall-regression，通过后才四类新out outputs/suite/standins-wallfix。新增Lux0/360。

停止前F2也已经终态：1眼84.06s、实际执行碰撞obstacle1/B，接触(7.097,-0.377,0.118)；其第一眼实际仅T1/A一个观测目标，没有B请求，真实扫描配准得到侧翻/缩小的A。原F2 summary与全部轨迹保留，不能当替身pass或真实Lux失败。无墙遗漏修复不会自动证明F2走通；必须回归后重新完成四类替身并检查该失败。F3在停止前刚启动，其部分数据也保留。

替身输入轴规范统一：旧单岩石直接导出扫描原始轴、多岩石已导出场景轴，不一致可能改变有限5°粗搜索的候选族。新offline exporter对所有场景/目标把真实扫描按当前观测水平轴旋转并底面居中（刚体变换、等比尺寸不变）；仍由生产注册估计全矩阵，不预置注册矩阵/不改搜索/门槛，实际Lux exporter完全不变。原所有standin输入/结果保留，新standins-wallfix四类统一使用此导出规则，不为F2单独调参；仍不保证F2到达，必须按完整结果判断。

原B4完整输入/扫描GLB/配准/预演/完整或部分轨迹外部包：/root/3d/artifacts/beforestep-r2/B4-before-wall-fix-complete.tar.gz，292061883 bytes，SHA256 32c580a2971ba066914e5f95d38a23d755d35589f6a6da2d2ead54e1e4af3783；公开失败身份evidence/suite/standins/before-wall-fix，全部offline/0paid。wall源码ed7c9ba已push，完整gate仍待replay终态，未启动新物理实验。

wallfix之后的非Lux同源校验预期：完整R1gate通过后，冻结11新场景全部四基线重跑（44次、workers1，与2个standin并行），旧60池/240运行和frozen.json选择依据完全保留；不改名单、不重分类选择。保守/see-dark/乐观预期与原相同；truth应到达，眼数/时间受虚构墙纠正的变化逐项保留。新manifest evidence/suite/regressions/wallfix-baselines/manifest.json，raw outputs/suite/baselines-wallfix；只验证同源对比、不新增场景/付费。

原F2碰撞复盘evaluate_suite_scene exit0，3D最小间隙0.0008718763999253496m、XY包络0.0m，公开before-wall-fix/F2_003的review/eval/physical文件，原archive仍精确保留打包时数据（补复盘JSON单独保留）。新替身导出QA exit0，三已观测真实扫描1000对顶点距离误差最大4.89e-8m/高度同/底面0/未供应配准矩阵；B4-wallfix-helpers-tests全66/66 exit0（2.597s）。

B7/helper预备支持公开wallfix-baselines完整44结果，与实际Lux source SHA相同；冻结分类/选择依据另保留，禁止更新frozen.json。当前仅compile，待完整B结果后真实数字审计，不冒称B7完成。

### B1预演墙配置修复：完整回归实际通过

源提交ed7c9ba，ops/预期/失败保全63ee1da已push且远端同SHA。`run_r2_regression.py --out outputs/qa/r2/B1-rehearsal-wall-regression --workers 3` 实际driver exit0；66/66单测（2.353s），6冻结配置SHA同；四基线stuck/arrived/collision/arrived、眼数/仿真时间同R1。R1原真实Lux重放1眼112.84s/无碰撞，12预演全部完整无碰撞，traj.npz全部数组与keys逐项同原，NPZ SHA 6b1481752708b9a2c9039ad91e55f98493714924afdd52da1be0baaee4758d1e相同。冷重配准墙钟1161.2s不含云排队，不是端到端延迟。公开gate evidence/suite/regressions/B1-rehearsal-wall/{regression.json,tests.log,driver.log}，完整原始输出仍outputs。

B4新统一导出/全链运行预期与同源44基线manifest已提交推送。现在允许开始新out outputs/suite/standins-wallfix（四类最早新D、workers2、每类含复盘）和outputs/suite/baselines-wallfix（冻结11全部四基线、workers1）。总3普通物理进程，0付费；源码ed7c9ba固定，旧B4原失败不覆盖，frozen.json不改。B4源同一gate/所有预演完整且无碰撞/独立到达/复盘四类全pass之后才真实Lux。

B1新gate提交d4dfb45aefb0e490875551458f12b43f492978ab已push0/远端同，启动前git status干净。B4新dispatcher PID2023174/tool41241、冻结同源基线PID2023248/tool29956实际运行；各自独立out/ledger及上述命令，三普通物理进程，0付费。旧B4与wall-regression父均已退出；这不是B4已通过，仍待新四完整链/复盘/所有预演检查。

### B4同源替身阶段结果与另一已冻结D的验证预期

F0_001新统一输入替身2眼139.48s到达、所有预演完整无碰撞，复盘exit0。F2_003新输入仍1眼84.06s撞B/obstacle1，接触(7.097,-0.377,0.118)；首眼只形成A的T1，B为0观测/0请求。其原/新替身全部保留，不冒称Lux失败或B4通过。F1_001第一眼预演没有虚构墙，但完整性失败waypoint_not_reached（误差0.469m）；流程正在第二眼继续。F3_002也在运行。原四类dispatcher结束后仍按所有预演与独立执行检查，不把中间失败删掉。

B4要求每类有一个决定性场景走通。最早D失败时，验证同类另一份已冻结的D：F2_007与F1_020；按原seed顺序、不改输入导出规则/参数/控制/场景config/冻结名单。两个失败场景依然必须进入B5完整真实组，不能替换、删除或隐藏；替身成功只证明该类链路能被执行，不能证明每个场景或Lux有效。预期同原：所有选定路线预演完整且无碰撞、≤2眼独立到达、复盘通过；若再次失败原样保存。新out outputs/suite/standins-wallfix/alternates/<scene>，regression B1-rehearsal-wall；每次单进程，当前memavailable约8GB，一新增约3GB，最多4普通物理进程，0paid。

B7报表helper已对保留R1与离线失败数据做只读QA：R1A6/6/6、B6/5/2不变；全程未形成请求的B保留0任务；共享目标保留共同task_id、不能双算独立任务。碰撞字段/接触记录优先于终态文字，不能以离散保存姿态正间隙或arrival字样抵消碰撞。三QA日志见evidence/suite/regressions/report-contracts，0新物理实验/0paid。真实B7仍未生成，helper不能冒充总表完成。

B5完整11真实场景dispatcher已实现并compile；在B4 summary不存在时实际被门禁挡住、API submit mock调用0次、真实out/budget均未创建（B5-dispatcher-gate-qa）。真实模式未启动。新版C1碰撞优先显示/计分在R1锚点真实浏览器exit0：五步、3回放、11候选/独立真值、无候选fixture、390px、0page/HTTP错误；完整场景组仍待B。

### B4初始四类同源运行完整终态（0paid）

新dispatcher已exit1，四个子完整链与复盘均exit0；当前初始gate all_passed=false：F0_001 2眼139.48s到达/完整预演；F1_001 2眼55.88s安全停车（第一眼预演waypoint未完成，第二眼无准入路线）；F2_003 1眼84.06s执行撞B；F3_002 2眼136.56s到达/完整预演。初始false gate保存为evidence/suite/standins/summary-initial-wallfix.json，全部新失败身份/事件/复盘在initial-wallfix，原完整二进制out不覆盖。

B4另两已冻结D正在真实形状全链：F2_007 PID2073848/tool63353、F1_020 PID2074134/tool51948，所有参数/控制/配准/两眼/5cm不改；sourceed7c9ba。原dispatcher已完全退出，不会再覆盖gate；两替身完成后才合并选择并做全四门禁。冻结11同源基线当前30/44（易变，以pool.json为准）。当前无真实Lux任务/0预算记录。docs/sandbox.md当前门禁命令已更新为B1-rehearsal-wall，避免克隆新源码后使用旧source SHA门禁。

### F2真实形状的配准诊断预期（0paid，不计套组真实结果）

F1_020替身1眼86.07s到达；F2_007替身2眼53.1s安全停车，第二眼实际505px/native_ok=false，B真形状注册后scale_ratio0.557/IoU0.4086，两批同字节12槽均0准入。目标B被看到，但当前注册估计侧翻并移位明显；不改冻结阈值或场景。

离线诊断在原F2_007同一观测/真实扫描上比较：已知真值放置仅用于诊断冻结自检能否通过；另用可见点云与候选的水平质心初始化，仍标准刚体/等比ICP、原评分和所有冻结门槛，不提供真值给这个初始化。目的是辨别“把可见最前点当完整物体最前点”的配准假设是否造成错误。诊断仅输出metrics，没有执行或Lux，不能作为B4通过。当前src仍ed7c9ba，完整R1gate通过；源码修改须在当前基线作业结束后、再完整R1gate。原首次初始化/全部失败都保留。

### B1第二处月坑配置遗漏定位（修改前证据）

真实放置仅用于离线诊断：F2_007的B真形状深度中位误差1.312mm/P95 4.189mm，几何和深度吻合；却因完整目标mask被截断，IoU0.5504被拒。可见质心初始化没有改善（IoU0.3963、free_intrusion0.374），不采用、不改配准算法或参数。进一步把遗漏且与B深度差<1cm的23131个像素反投影，23101个（99.8703%）落在已知月坑禁行格。capture.py中targets_from_map和grow使用prior_nogo原来只想排除大石堆，B1加入月坑后把岩石伸进坑沿禁行格的真实可见部分也排除了。诊断/源脚本/原始输出公开evidence/suite/regressions/crater-target-clipping，0Lux/0运动实验。

修复决定：从同一场景配置分出target_exclusion_mask，只排除原窄道/已知右墙；prior_nogo继续叠加月坑原半径+5cm，所有策略依然不能驶入坑。岩石目标检测/同一grow3掩码使用前者，保留原ROCK_Z、min_cells、RGB-D、亮度阈值、native512/两眼/规则控制/所有JSON门槛与场景配置。不是改变相机或给规划器真值；只恢复原观测已存在的岩石像素。缺省旧四场景完全同。

所有旧物理作业/两个alternate/44同源基线已结束后才改源。运行前预期：新增跨坑沿ROCK目标完整提取，规划禁行阵列原字节不变；全单测和完整五R1gate/全部NPZ数组同原。新独立out outputs/qa/r2/B1-crater-target-regression，通过并push后才新四类全链（统一当前源，F0_001/F1_020/F2_003/F3_002）、新11四基线；原/新失败/原基线完整保留。新增Lux仍0/360，冻结12名单不动，不为单场景调参。

修复后的保留观测单测重建exit0：同一RGB-D、同一真实诊断放置，目标mask29399→52882px，恢复91个坑禁行格内的ROCK观测格；IoU0.5504→0.9893，depth median1.217mm/P954.890mm。没有新运动或Lux；原/新mask和figure/after-unit.json在crater-target-clipping，不能当新套组结果。当前新67单测2.129s通过，四R1非Lux基线全部同原；完整真实重放仍在源gate中计算，不运行新场景或收费。

新源cfffaf8已push（SRC map/capture）；67tests和四R1基线通过，完整replay仍待。下一B4样本预期写入crater-target-selection.json：F0_001/F1_020/F2_003/F3_002；同一当前源/原真形状导出/原完整链，不改冻结12清单。初始F1_001安全停车仍保留且仍在B5中。新44基线manifest在regressions/crater-target-baselines，out outputs/suite/baselines-crater-target；新B4 out outputs/suite/standins-crater-target。全部前先等B1-crater-target-regression完整pass并push，当前不启动。B5/B7默认指向该新同源基线，不混用旧source数据；旧44完整结果仍保留wallfix-baselines。

### B1月坑目标过滤修复：完整回归通过与恢复检查点

源码cfffaf8与运行预期e22dc2c均已push/远端e22dc2cdc681e916dac1fa19ae1eedfcd61ba8ea。`run_r2_regression.py --out outputs/qa/r2/B1-crater-target-regression --workers 3` 实际exit0；67/67单测2.129s、6冻结配置SHA同，四基线结果/眼数/时间同R1。真实Lux原数据reuse一眼112.84s、12预演完整无碰撞，traj.npz全部5数组与键集合逐项同原，NPZ SHA6b1481752708b9a2c9039ad91e55f98493714924afdd52da1be0baaee4758d1e相同。此次冷重放1139.3s不含云队列，不是端到端延迟。公开gate evidence/suite/regressions/B1-crater-target/{regression.json,tests.log,driver.log}。

服务进程重启发生在gate结束后、保存回执之前。实际核查：main与远端e22dc2c同、工作区干净；旧gate/44基线/全部替身/alternate均终态，无存活物理或云作业。没有重跑已完成gate或创建任何Lux任务。此回执push后继续新四类完整standin和新44同源基线，源cfffaf8保持固定；新B4全四通过/复盘0后才B5真实Lux。docs/sandbox当前全链例子已更新为此有效gate。新增Lux0/360。

新完整gate提交6fb2423de031f38fb1ea93de9a8aee3b9aa0d2d4已push0/远端同，启动前git status干净。新B4 parent2076238/tool88791、44基线parent2076311/tool99784已实际运行，sourcecfffaf8保持不变，ledger/log上述独立out，3普通physics；0paid。服务重启前结束的gate没有重启；B4全新完整验证尚待结果。

旧B4-wallfix四个完整初始运行+两个完整alternate的原GLB/观测/配准/预演/轨迹已外部保全：/root/3d/artifacts/beforestep-r2/B4-wallfix-and-alternates-complete.tar.gz，483680028bytes，SHA256 230e3ea03a5cd495a71d2ed0678553e47bdd539b80dc87310d322c31a451072d，tar exit0。公开initial-wallfix/archive.json与alternates-wallfix两份完整身份/事件/复盘；全部not_real_lux/0paid。新当前源B4与44仍在计算，旧数据包不包含新运行，也不覆盖旧错误记录。

C1浏览器验收另加入纯UI fixture：保留实际首关扫描/轨迹，仅在被拦截的测试载荷中令imagination result=arrived且带原乐观接触记录，要求显示碰撞且玩家/想象固定策略均不计通过。实际实验JSON不变；该新增验收分支目前仅compile，待C1全组真实浏览器验证后才标完成，不计新实验。

### 阶段 B4 小结（§8）

1. 完成并验证：SRC cfffaf8；完整R1gate提交6fb2423、67tests2.129s/6冻结SHA/五运行/原5轨迹数组与NPZ SHA同。当前四类source==R1gate，run_suite_standins driver exit0/四child与review均0：F0_0012眼139.48s、F1_0201眼86.07s、F2_0032眼142.74s、F3_0022眼136.56s全部独立到达且无碰撞；各1个完整无碰撞预演格。公开standins/summary.json和crater-target中的身份、事件、复盘、每scene SHA清单；原始out standins-crater-target。远端main此前9faed59（已push0），本小结/证据提交后继续。
2. 做了未验证：B5 dispatcher仅compile/门禁mock，尚未运行真实新Lux；新44同源基线还在跑；C1/C2只有原R1锚点基础，完整组待真实数据。
3. 失败保留：最初虚构右墙、F1_001停车、F2_003碰撞、F2_007真形状0准入都在before-wall-fix/initial-wallfix/alternates-wallfix及完整外部数据包，没有被替换成新成功。
4. 自决：按B4修两处场景配置程序遗漏；原mask删掉23101个坑禁行格内可见岩石像素，修复后同保存观测IoU.5504→.9893。所有阈值/控制/相机/场景/5cm/两眼不动；F1用同类另一已冻结D走通，B5仍保留全部12原名单。时间关口未到，不提前收缩。
5. 新Lux0，累计0/360；全部替身not_real_lux、unused slots不是服务商失败。
6. 新B4和外包均终态；baseline父2076311/tool99784仍在跑，当前约20/44（易变）。源码固定cfffaf8，提交前仅本回执/已compile C1 fixture改变。
7. 下一动作：本小结与B4 gate push并核远端，启动run_suite_real.py --regression evidence/suite/regressions/B1-crater-target/regression.json --workers2，冻结11个新场景真实Lux；每sample先账本，再create，360上限、known/uncertain只query。

新B4完整二进制数据外包：/root/3d/artifacts/beforestep-r2/B4-crater-target-complete.tar.gz，328443345bytes，SHA256 81269163c2a67fbc2b3530d7c2a5589b72b80f6ba021ee2c98e08e0b5317a9ac；tar exit0/每scene public set远小于150MB。Source/目标输入/原扫描GLB/配准/全部预演/执行/复盘都保全，供负责人渲染，未渲染新Demo视频。

B5真实dispatcher PID2077882/tool60090已启动并实际创建任务。账本快照：新付费容量使用10/360，状态{'ok': 3, 'pending': 7, 'not_submitted': 1}；C.client/Budget记录在create前已有identity，API key仅进进程环境。not_submitted是并发限制明确拒绝的请求，不当作已付费；已知/不确定只query，不重复create。权威仍outputs/generation/r2-budget.json与outputs/generation/tasks，实时数以ledger为准，SRC固定cfffaf8。

新增C1 contact-priority UI fixture在真实浏览器已exit0：原锚点五步/3回放/11候选/独立truth、无候选回退、390px与0page/HTTP错误均通过；合成arrival+contact载荷显示碰撞、玩家和imagination均0/1，实际实验文件未修改。最新anchor-game/browser.json记录contact_priority_verified_with_ui_fixture=true。仅1锚点，不充作完整12关完成；SRC仍逐文件同67测试/五R1gate版本cfffaf8。

新11场景44同源非Lux基线全部exit0/completed=true；与修目标mask前的44运行逐项比较，所有traj.npz键和全部数组完全相同。说明此修复保留了全部场景的控制、机器人、传感器和导航禁行行为。新原结果public evidence/suite/pool/crater-target-baselines/manifest_results.json；比较44/44通过，regressions/crater-target-baselines/comparison.json，原旧44保留。新源cfffaf8与真实Lux正在使用的source一致，未重新筛选冻结场景。baseline parent2076311已退出；只剩真实dispatcher2077882/live，SRC不改。

恢复核验（2026-11-10 22:56 UTC）：main本地/远端6c8c8f8同；只一个本项目写会话。实际重新逐项加载新/旧44份traj.npz，全部keys/arrays精确相同，current SRC SHA == B1-crater-target完整R1gate == B4 allpass == 新44基线，exit0（同既有PYTHONPATH）。首调用漏临时依赖路径exit1，补回路径后验证通过，无源码/实验改动。B5父2077882仍存活，两个F0场景处于注册/自检/物理链；此时budget24/360且24全部ok，不新建重复任务。新增candidate GLB仍由运行生成、暂未提交；整scene完成后按§2.5外部完整包+≤150MB精简集保全。三个时间关口未到，继续全12组。

B6调度决定（真实B5仍运行，未更改src）：使用单个普通Python后处理父进程，按冻结seed顺序处理已完成并复盘exit0的场景，每场枚举全部每眼拒绝候选；B5运行期间最多1个CF物理子进程，B5全部结束后最多3个。当前16GB内存、B5两子各约3GB，此调度保持总约3个物理子，减少长注册阶段的空等，不改任何实验参数/数据/名单、不新增paid。每个第二眼CF追加只读核验：原/CF第二眼时刻与实测姿态及此前traj.npz全部5数组精确相同；不把未来候选放入首眼。数据保全仍在每scene全部CF终态后一次生成SHA manifest/完整外包，未完成的场景不冒称结果。

B6后处理调度与前缀核验已实现，ops三个文件compile exit0；只读QA在保存的R1真实形状第二眼CF上，原第二眼时间/实测姿态和全部5个prefix数组精确同，故意改1mm qpos的隔离副本正确被拒，public regressions/report-contracts/CF-prefix-audit.json。0新物理/0新paid，SRC与完整R1gate逐文件SHA仍相同。报告生成器同时纠正上限说明：保守/see-dark/乐观最多5眼，真实形状/真实Lux最多2眼；这只是忠实说明既有流程，不更改上限。新全组B6尚未执行，等待已完成真实scene。

C2浏览器新增扫描库真实drag/drop验收exit0（C2-library-drop-anchor.log）：rock_07从库拖到(10,-1.5)并从导出JSON核对相同；既有岩石拖动/旋转/高度、坑增删、太阳、三路线、390px和0page/HTTP错误都通过。public presentation/sandbox-anchor/browser.json仍明确development_anchor_only=true，只有1个R1首关，完整12组C2尚未验收。

B5中间观测（不是导航终态）：F0_001实际B第二眼527px/native_ok=true，但B首眼native_ok=false，正确调用新视角img六份；F0_005实际A第二眼1249px且两眼native_ok都true，正确调用imgs三份，B336px/native_ok=false调用新img六份。原请求字节与sample/task identity保存在真实out/budget，public regressions/report-contracts/real-second-eye-intermediate.json列出原请求路径与字段。此时33/360（29ok/4pending），完整源cfffaf8，两个真实父子和B6等待父继续运行；不得把补看输入成立写成到达。
