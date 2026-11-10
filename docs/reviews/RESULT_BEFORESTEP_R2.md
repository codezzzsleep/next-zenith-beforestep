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
| B1 | 地形/太阳配置与完整回归 | 完成 | 本次global-stop源修正与完整五回归通过；65测试 |
| B2 | 参数预注册、生成器、候选池分类 | 进行中 | 96fa0b7/4f554c7/671a4e6；v3配置31ef28c，现有池运行中 |
| B3 | 冻结场景组并推送 | 未开始 | — |
| B4 | 四类真实形状替身完整链 | 未开始 | — |
| B5 | 场景组真实Lux3D | 未开始 | — |
| B6 | 全部场景复盘和全部拒绝反事实 | 未开始 | — |
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
