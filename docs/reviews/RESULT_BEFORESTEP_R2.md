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
| B1 | 地形/太阳配置与完整回归 | 完成 | 原96fa0b7；最终修复回归见B1-final与本次提交 |
| B2 | 参数预注册、生成器、候选池分类 | 进行中 | 参数/生成器本次先提交；尚未运行池 |
| B3 | 冻结场景组并推送 | 未开始 | — |
| B4 | 四类真实形状替身完整链 | 未开始 | — |
| B5 | 场景组真实Lux3D | 未开始 | — |
| B6 | 全部场景复盘和全部拒绝反事实 | 未开始 | — |
| B7 | 完整总表 | 未开始 | — |
| B8 | 预定规则结论 | 未开始 | — |
| C1 | 五步关卡模式 | 未开始 | — |
| C2 | 沙盒与一致性 | 未开始 | — |
| C3 | 导出与人工场景 | 未开始 | — |
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
