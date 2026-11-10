# RESULT_BEFORESTEP_R1

执行依据：[REVIEW_BEFORESTEP_R1.md](REVIEW_BEFORESTEP_R1.md)。主线为 `stress_v8`（A+B）、终点 `(10.5,0)`、规则控制器。冻结几何、太阳、传感器链、自检门槛、5 cm余量与两眼上限保持。本文在每次运行之前记录预期，之后保留原始终态并逐项对照。

## 提交与当前阶段

- `fdcf629`：按复核§7纳入训练控制附录与文献/同图审计；主线不使用训练控制或姿态模型。
- `7b6f5b4`：复核原文SHA256 `0541ef2d38d695e7b6efd044ef6c64ed47cf0b89b7fd4aff50725a7ea36eed29`，与附件逐字节一致。
- `73430ec`：§2.0预注册及stress_v8的purpose主展示标记；实际运行均以此源码启动。
- 当前阶段：§2.0及最终源码复核四项通过；§2.1–§2.3实现、38单测和有界追加流程完成。完整注册替身未到达，因此真实Lux3D调用尚未开始，§2.5及§3尚未验收。

## §2.0 预注册（运行前）

所有运行使用相同 `stress_v8`、规则控制器、原起点和终点；从完整场景起点开始，采用当次实时仿真传感器。

公共环境：`PYTHONPATH=/tmp/lunar-review-20261109-deps:/tmp/beforestep-browser-deps:src PYTHONDONTWRITEBYTECODE=1 MUJOCO_GL=egl MPLCONFIGDIR=/tmp/beforestep-r1-matplotlib OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1`。

| ID | 命令（公共环境之后） | 运行前预期，按§2.5 | 状态 |
| --- | --- | --- | --- |
| R1-20-C | `python3 -m beforestep run --scene stress_v8 --controller-model rules --policy conservative --max-looks 5 --out outputs/reviews/r1/section20/conservative` | 无可规划路线而停车，最多5眼；无碰撞 | 尚未运行 |
| R1-20-D | `python3 -m beforestep run --scene stress_v8 --controller-model rules --policy conservative --see-dark --max-looks 5 --out outputs/reviews/r1/section20/see_dark` | 到达，≤5眼，无碰撞 | 尚未运行 |
| R1-20-O | `python3 -m beforestep run --scene stress_v8 --controller-model rules --policy optimistic --out outputs/reviews/r1/section20/optimistic` | 碰撞；复盘出发前规划路线的车身压入真实岩石≥10 cm | 尚未运行 |
| R1-20-T | `python3 -m beforestep run --scene stress_v8 --controller-model rules --policy imagination --imagine truth --max-looks 2 --out outputs/reviews/r1/section20/truth` | 替身链到达；逐候选完整预演无碰撞；≤2眼 | 尚未运行 |

真实形状仅用于本表明确标注的替身检验及复盘，不作为真实Lux3D成功证据。预期不因运行结果修改。若四项不一致，按§2.0恢复旧提交`c3bb5848f`逐项比对并修正移植；仍不同则原样记录后继续。

## §2.1–§2.5 与§3

此处为启动前的规则登记；实际执行和未完成项见后文。每个新运行/付费批次在启动前于此登记。第二眼B输入不足时仍按§2.2单图6份，0采纳仅追加同字节一批6份；合计12份仍0安全停车并进入预注册§2.4。没有新增场景、放宽门槛或第三眼的授权。

## §2.1–§2.3 实现与替身验证预注册（运行前）

- `89421e2`：四项原始数据与结果保全，49个去重LFS对象84,273,178 bytes已上传、verify并再次查询确认可下载；main已同步。
- 第二眼选点只用目标观测格及map.zmax中的可见高度，朝向对准观测格中心；相机距目标最近格<0.8 m按§2.1正文排除；≥512 px的点先于全部不达标点。无达标可达点时保留原排序低分辨率候选并如实记录。`target=None`完整74候选排序在修改前冻结并用于回归。
- 两眼native_ok同时为true才发两图M1–M3，否则第二眼单图6份；追加批次是独立retry目录中的A1b…C2b，输入使用首次批次实际上传路径/字节，原始请求/结果保留。合计12份仍0时固定安全停车，不能继续采样或第三眼。
- R1的stress_v8执行只预演将要执行的路线；旧程序新增的“无生成参照路线预演”不属于原V8主线，保留在历史gate附录；§2.0旧参照碰撞数据仍完整保留。

替身验证命令（公共环境同§2.0）：

`python3 -m beforestep run --scene stress_v8 --controller-model rules --policy imagination --imagine lux --reuse-lux outputs/reviews/r1/standin_source --max-looks 2 --out outputs/reviews/r1/section21_standin`

运行前预期：第一眼复用冻结的已有任务，A有准入、B全拒绝；第二眼选点使B预计≥512 px，实际采集记录crop_native_px；因第一眼251 px，生成单图6份请求，退出码10。替身结果在该请求中显式标为standin：只提供真实B网格的一份可用候选，其余5份为测试用失败状态；之后完整重启同命令，观测字节必须匹配，配准、自检、全部执行路线预演通过并≤2眼无碰撞到达。整个验证不创建任何付费任务，不计真实Lux3D成功。

同一替身输出另设独立retry验证：第二眼首批6份都为测试用失败状态，预期自动生成且只生成一次同字节6份A1b…C2b并退出10；补入一份真实B替身后合计12判断，≤2眼完成预演并到达。另一单元测试将两批都失败，核对无第三批请求。每份替身状态及判断原样保存。

## §2.0 实测结果（预期保持原文）

四次退出码均为0。保守为stuck/5眼、see-dark到达/3眼、乐观碰撞/1眼、真实形状替身到达/1眼。四项满足§2.0，可以进入§2.1；不需要触发旧代码差异核查。原始文件逐SHA256复制核对完成，见各运行preservation.json。

乐观出发前计划路线的已有栅格复盘drive_margin_m=-0.230 m，超过§2.5要求的10 cm压入；后续§2.5仍会独立按连续路线/真实几何计算。替身的执行路线预演completed=true/collided=false；原代码附加的无生成参照路线预演发生碰撞，单独保存，不能把它称为通过的执行预演。

### conservative

命令：`python3 -m beforestep run --scene stress_v8 --controller-model rules --policy conservative --max-looks 5 --out /root/3d/next-zenith-beforestep/outputs/reviews/r1/section20/conservative`

退出码：`0`。运行身份/原数据：[conservative](../../evidence/reviews/beforestep_r1/section20/conservative/run_identity.json)。

summary.json 原文：

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
  "wall_s": 101.9,
  "collision": null
}
```

### see_dark

命令：`python3 -m beforestep run --scene stress_v8 --controller-model rules --policy conservative --see-dark --max-looks 5 --out /root/3d/next-zenith-beforestep/outputs/reviews/r1/section20/see_dark`

退出码：`0`。运行身份/原数据：[see_dark](../../evidence/reviews/beforestep_r1/section20/see_dark/run_identity.json)。

summary.json 原文：

```json
{
  "policy": "conservative",
  "tag": "conservative",
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
  "wall_s": 95.3,
  "collision": null
}
```

### optimistic

命令：`python3 -m beforestep run --scene stress_v8 --controller-model rules --policy optimistic --out /root/3d/next-zenith-beforestep/outputs/reviews/r1/section20/optimistic`

退出码：`0`。运行身份/原数据：[optimistic](../../evidence/reviews/beforestep_r1/section20/optimistic/run_identity.json)。

summary.json 原文：

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
  "wall_s": 67.2,
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

### truth

命令：`python3 -m beforestep run --scene stress_v8 --controller-model rules --policy imagination --imagine truth --max-looks 2 --out /root/3d/next-zenith-beforestep/outputs/reviews/r1/section20/truth`

退出码：`0`。运行身份/原数据：[truth](../../evidence/reviews/beforestep_r1/section20/truth/run_identity.json)。

summary.json 原文：

```json
{
  "policy": "imagination",
  "tag": "imagination",
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
  "wall_s": 122.5,
  "collision": null
}
```

### 单元测试与purpose清单同步

首次全套单测34项中33通过、1失败：原assets/manifest.json仍保留修改purpose前的stress_v8.json SHA。按复核§1更新当前清单SHA，原配置从fdcf629逐字节保存到evidence/reviews/beforestep_r1/frozen_before_r1/stress_v8.json，并核对除purpose外全部字段相同。未修改物理场景或门槛；失败日志outputs/reviews/r1/r1_unit_tests.log保留。下一次测试另存日志，不能覆盖第一次。

### 替身第一次启动的输入核对

上面预注册的旧首眼复用命令实际退出11：新传感器的首眼RGB/深度/掩码与历史reference_v8的SHA不同，程序正确拒绝复用，没有付费请求。实际车姿态相同，但不能把不同图当成同图。失败目录section21_standin及日志保留。处理按原输入保管规则：另外开一个独立fresh替身目录，使用当次实际观测；旧首眼不强行复用、不重创建旧任务。

fresh替身命令（公共环境同§2.0）：

`python3 -m beforestep run --scene stress_v8 --controller-model rules --policy imagination --imagine lux --max-looks 2 --out outputs/reviews/r1/section21_standin_fresh`

启动前预期：首眼写两个六份单图请求并退出10。测试提供A真实形状替身及B历史被拒几何替身（其余测试状态为failed），通过实际配准与原自检使A准入、B拒绝，随后第二眼为B单图6份并退出10。为第二眼提供真实B替身后，完整预演和执行≤2眼无碰撞到达。所有模拟任务标为offline standin，绝不计为真实Lux结果。本轮任何新真实首眼任务将在这条完整替身链与全部单测通过之后才创建。

### 第二眼替身准备的实际数字

修改后的34项单测最终全部通过（r1_unit_tests_final.log，exit0）。fresh首眼準備exit10；首眼替身A1真实A轮廓IoU0.9328/尺度1.0112准入，B历史拒绝替身IoU0.4747/尺度0.6351拒绝。随后第二眼选点请求(4.0917097567,0.4)、朝向-1.791°，预计513.3881 px；实际车停(4.0749528127,0.3970295502)、朝向-0.7709°，B crop_native_px=506，native_ok=false，仍按§2.2单图6份，exit10。预期与实际差异原样记录：像素估计达标，实际差6 px；不改点、不追加第三眼、不改512门槛。

下一次完整替身执行使用同一命令，第二眼6份中A1为真实B网格、其余5份为测试用失败状态。运行前预期仍为原观测SHA匹配、原自检准入、完整执行预演且≤2眼无碰撞到达。

### §2.3独立替身分支的运行标签

以下标签对应此前已经预注册的追加采样和全拒绝分支，不改变预期：

- retry命令：`python3 -m beforestep run --scene stress_v8 --controller-model rules --policy imagination --imagine lux --reuse-lux outputs/reviews/r1/standin_validated_first_source --max-looks 2 --out outputs/reviews/r1/section23_retry_standin`。准备第二眼退出10；填第一批6个failed后，下一次同命令应只写6b并退出10；填一份真实B替身后合计12判断，应≤2眼完成预演并到达。
- 全拒绝命令：`python3 -m beforestep run --scene stress_v8 --controller-model rules --policy imagination --imagine lux --reuse-lux outputs/reviews/r1/standin_validated_first_source --max-looks 2 --out outputs/reviews/r1/section23_zero_standin`。同样首批6个failed→只写6b→退出10；第二批仍6个failed，下一次应stuck/2眼/无碰撞且无第三批。这里是离线控制流测试，不能据此在真实场景执行§2.4替换。

### 单图替身全流程的实际终态（不符合预注册到达预期）

最后一次同命令退出0，但result=stuck、2眼、无碰撞。A准入，第二眼真实B替身A1也通过自检（IoU0.9300、尺度1.0256），原5 cm余量规划结果low_margin，因此没有执行路线。不能把此结果算作到达。

summary.json原文：

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
  "scene_id": "stress_v8",
  "goal": [
    10.5,
    0.0
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 53.68,
  "sensor_mode": "live",
  "looks": 2,
  "final_pose": [
    4.075,
    0.397,
    -0.69
  ],
  "sim_time_s": 54.88,
  "wall_s": 156.4,
  "collision": null
}
```

赛后替身几何诊断在standin_geometry_diagnostic.json：同一个第二眼地图/同一起点，真实A+真实B和注册A+真实B都有路线；真实A+注册B与注册A+注册B均无5 cm余量路线。注册B占地x=[6.175,7.475]、y=[-0.375,0.775]，该诊断不进入生产规划。问题不是A，也不是改变终点；目前是B通过自检但配准占据仍留不出余量。按§0.3不降低门槛，不自行扩大§2.4替换条件。

追加采样及全零分支已按前述预期各产生且只产生一次6b请求，准备过程退出10，输入路径/SHA与首批逐项相同。下面的续跑仍按已预注册预期核对；不因单图替身失败而修改任何预期。

## 真值隔离与最终源码复核的运行前预期

生产保守/乐观/Lux模式现在不构建真实几何占据，也不在运行中计算隐藏真值余量；这些数字统一由赛后build_eval.py生成。明确的--imagine truth检验模式仍允许真实形状替身，物理环境保留真实障碍用于独立执行和接触检查。为核对该隔离及当前源码，另存section20_final，使用与§2.0相同的四条命令，仅--out换成outputs/reviews/r1/section20_final/<case>。预期仍是保守stuck≤5眼、see-dark到达≤5眼、乐观碰撞且计划压入≥10 cm、truth检验到达≤2眼且全部执行预演无碰撞。结果不会覆盖初次§2.0数据。

站位/追加采样/真值隔离/离线任务身份防混入的单元测试在r1_final_boundary_tests.log；真实Lux调用依旧没有开始。离线单图替身与追加一份候选的替身未到达，因此还不能宣布完整注册替身链通过，不能花钱继续生产生成。

## 恢复后核验与源码提交

- `719e1ce`：§2.1目标选点、§2.2输入模式、§2.3一次追加与74候选黄金回归。
- `00e9a41`：追加预注册排除运行数组，首眼历史目标不误触发第二眼追加。单批、追加一份和全零替身的52份源码SHA均逐项匹配此提交；旧输入不一致运行匹配719e1ce。
- `974c37b`：生产保守/乐观/Lux不推导隐藏真值，赛后单独复盘；付费客户端拒绝离线替身身份。最终四项基线的52份源码SHA逐项匹配此提交，38项单测通过。原始运行的identity和文件没有为匹配提交而改写。
- [逐文件核验](../../evidence/reviews/beforestep_r1/preservation_audit.json)：初次与最终四项基线的全部轨迹数组逐项完全相同；原始输入/输出、离线共享GLB与源身份均核验。第一次单测失败、复用输入失败和替身未到达均保留。

### 最终源码四项复核：命令、退出码、summary原文

公共环境仍为§2.0所列；以下运行前预期已在“真值隔离与最终源码复核”登记，未因终态调整。

#### conservative

命令：`python3 -m beforestep run --scene stress_v8 --controller-model rules --policy conservative --max-looks 5 --out /root/3d/next-zenith-beforestep/outputs/reviews/r1/section20_final/conservative`。退出码：`0`。数据：[运行身份](../../evidence/reviews/beforestep_r1/section20_final/conservative/run_identity.json)、[eval](../../evidence/reviews/beforestep_r1/section20_final/conservative/eval.json)。

summary.json原文：

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
  "wall_s": 97.9,
  "collision": null
}
```

无可规划路线而停车/5眼/无碰撞，符合原预期。

#### see_dark

命令：`python3 -m beforestep run --scene stress_v8 --controller-model rules --policy conservative --see-dark --max-looks 5 --out /root/3d/next-zenith-beforestep/outputs/reviews/r1/section20_final/see_dark`。退出码：`0`。数据：[运行身份](../../evidence/reviews/beforestep_r1/section20_final/see_dark/run_identity.json)、[eval](../../evidence/reviews/beforestep_r1/section20_final/see_dark/eval.json)。

summary.json原文：

```json
{
  "policy": "conservative",
  "tag": "conservative",
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
  "wall_s": 96.8,
  "collision": null
}
```

到达/3眼/无碰撞，≤5眼；XY车身包络最小间隙0.0870334 m。

#### optimistic

命令：`python3 -m beforestep run --scene stress_v8 --controller-model rules --policy optimistic --out /root/3d/next-zenith-beforestep/outputs/reviews/r1/section20_final/optimistic`。退出码：`0`。数据：[运行身份](../../evidence/reviews/beforestep_r1/section20_final/optimistic/run_identity.json)、[eval](../../evidence/reviews/beforestep_r1/section20_final/optimistic/eval.json)。

summary.json原文：

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
  "wall_s": 66.0,
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

按5 mm间距复盘原计划：车身中心距真实B最近0.1110114 m，半车宽0.33 m，压入代理量0.2189886 m ≥0.10 m，满足原要求；独立执行有真实碰撞。

#### truth

命令：`python3 -m beforestep run --scene stress_v8 --controller-model rules --policy imagination --imagine truth --max-looks 2 --out /root/3d/next-zenith-beforestep/outputs/reviews/r1/section20_final/truth`。退出码：`0`。数据：[运行身份](../../evidence/reviews/beforestep_r1/section20_final/truth/run_identity.json)、[eval](../../evidence/reviews/beforestep_r1/section20_final/truth/eval.json)。

summary.json原文：

```json
{
  "policy": "imagination",
  "tag": "imagination",
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
  "wall_s": 103.1,
  "collision": null
}
```

到达/1眼；执行预演全部完成且无碰撞。实测yaw下XY车身包络最小间隙0.0952750 m；仅是替身检验，不计真实Lux结果。

### §2.3两条独立离线分支：实际终态

两条分支均为首批6份failed→追加一次同字节6b并退出10→补齐后同命令续跑退出0。该流程真实发生在运行中；替身身份明确与付费任务隔离。

#### retry_one_candidate

命令：`python3 -m beforestep run --scene stress_v8 --controller-model rules --policy imagination --imagine lux --reuse-lux outputs/reviews/r1/standin_validated_first_source --max-looks 2 --out outputs/reviews/r1/section23_retry_standin`。阶段退出码：准备`10`、一次追加`10`、最终`0`。数据：[运行身份](../../evidence/reviews/beforestep_r1/standins/retry_one_candidate/run_identity.json)。

summary.json原文：

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
  "scene_id": "stress_v8",
  "goal": [
    10.5,
    0.0
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 53.68,
  "sensor_mode": "live",
  "looks": 2,
  "final_pose": [
    4.075,
    0.397,
    -0.69
  ],
  "sim_time_s": 54.88,
  "wall_s": 135.3,
  "collision": null
}
```

两批12份中第二批A1b为真实B替身、其余11份failed。A1b准入（IoU0.9300、尺度1.0256），但low_margin无执行路线；stuck/2眼/54.88s/无碰撞，**不符合预注册到达预期**。这一分支验证追加结果参与配准与合计判定，未验证到达；没有第三批。

#### retry_all_rejected

命令：`python3 -m beforestep run --scene stress_v8 --controller-model rules --policy imagination --imagine lux --reuse-lux outputs/reviews/r1/standin_validated_first_source --max-looks 2 --out outputs/reviews/r1/section23_zero_standin`。阶段退出码：准备`10`、一次追加`10`、最终`0`。数据：[运行身份](../../evidence/reviews/beforestep_r1/standins/retry_all_rejected/run_identity.json)。

summary.json原文：

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
  "scene_id": "stress_v8",
  "goal": [
    10.5,
    0.0
  ],
  "start_mode": "scene_start",
  "execution_elapsed_s": 53.68,
  "sensor_mode": "live",
  "looks": 2,
  "final_pose": [
    4.075,
    0.397,
    -0.69
  ],
  "sim_time_s": 54.88,
  "wall_s": 81.8,
  "collision": null
}
```

12份全部failed/0准入，sampling_stop明确记录total_samples=12、action=safe_stop_then_review_section_2_4；stuck/2眼/54.88s/无碰撞、无第三批，符合此分支安全停止预期。测试failed是控制流替身，不能推出Lux无法生成，也不能据此触发真实§2.4替换。

## 对照§2.5与剩余依赖

| 条件 | 当前结论 |
| --- | --- |
| 保守≤5眼规划不出路线、停车 | 初次和最终源码均通过 |
| see-dark同控制到达≤5眼 | 两次均到达/3眼，无碰撞 |
| 乐观碰撞、原计划压入≥10cm | 两次均碰撞；计划压入21.8989cm |
| 真实形状检验到达 | 直接truth检验两次到达；**经实际配准的完整B替身仍未到达** |
| 真实Lux≤2眼到达、全部预演完成且无碰撞 | 未运行，不能宣称通过 |
| 真实Lux完整reuse、终态/轨迹一致 | 未运行 |
| B首眼全部被拒候选逐一trust反事实 | 待真实首眼结果，不挑选；当前不声称自检挡住碰撞 |
| §3报告与首页改写 | R1权威/历史附录入口已改；最终主线数字与叙事待验收，未完成 |

截至该检查点的两个实际依赖（联网恢复见后文）：其一，当时受限执行环境对api.aholo3d.cn的DNS再次gaierror/-3，已有终态任务的只读GET有限重试失败，见[联网记录](../../evidence/reviews/beforestep_r1/connectivity.json)；不缺付费授权且没有新create。其二，注册替身B准入但low_margin，§2.4只覆盖真实12份0准入，未覆盖此结果。按§0.3先提交完整证据后请求负责人给出此情况的处理规则；不改场景、门槛、5cm或替换触发条件，不拿替身当真实Lux成功。

代码与文档的空白检查通过；初次失败单测的原始日志有一处行尾空格，按原始证据保管规则保留字节，不为格式检查改写失败日志。

## 本阶段数据同步与§0.3待补充规则

- `b817c1b`：完整替身失败、最终四项基线、赛后eval和原日志/轨迹/观测/配准数据提交，562文件；此前719e1ce、00e9a41、974c37b共四提交已原生fast-forward到main，没有改写历史。
- 112个相关去重LFS对象合计182,591,264 bytes已确认服务器可用；本阶段新增上传46个/64,868,005 bytes，上传verify后再次batch查询无待传。2223文件的远端树未截断，tree `aff2dd3a6b343a87148355a5ee869d1d3f0c6a6b` 与本地完全一致。
- 主线仍未成立：注册B替身通过自检却low_margin停车，真实Lux和§2.5反事实/重放、§3最终首页报告仍未执行。没有新付费任务，不自制Demo视频。

请负责人按§0.3补充“准入但low_margin”的处理规则：是否先在冻结场景和全部冻结门槛下排查、修正配准实现，并预注册重跑完整替身链？同时需要恢复可调用Lux3D的执行环境；当前实际DNS/只读GET失败已有证据。§2.4的真实12份0准入触发条件保持，不用离线failed替身扩大该例外。

## 联网恢复后的只读核查预注册

用户已恢复联网。先只读查询既有终态任务5125592，预期DNS及真实API认证成功；不新建任务。随后只读比较已保留的B真实替身和其配准矩阵，量化世界平移、旋转、尺度及导航占据变化；预期定位既有low_margin的几何来源，不修改配准、准入或规划规则。这是赛后诊断，真值不进入生产决策。

### 联网恢复与只读诊断结果

- 只读API查询命令：`PYTHONPATH=/tmp/lunar-review-20261109-deps:/tmp/beforestep-browser-deps:src python3` 中调用 `client.api("GET", "/lux3d/v1/generate/task/get?taskid=5125592", timeout=15)`；退出0。DNS解析及认证成功，旧任务status=3。实际时间和结果见[connectivity_restored.json](../../evidence/reviews/beforestep_r1/connectivity_restored.json)。没有create或新付费任务；旧联网失败证据保留，当前联网依赖已解除。
- 赛后只读诊断命令：`PYTHONPATH=/tmp/lunar-review-20261109-deps:/tmp/beforestep-browser-deps:src PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 evidence/reviews/beforestep_r1/diagnose_standin_registration.py`；退出0，[完整数字](../../evidence/reviews/beforestep_r1/standin_placement_diagnostic.json)。B原世界偏航-26°，配准后-29.2925°；三维旋转偏差3.3651°、XY平移偏差0.0202528 m、等比尺度1.0204609。该矩阵在生产过程中仅由观测求得；这里的真实矩阵只用于赛后诊断。
- 同一个二眼观测地图/同一实际起点/真实A/原5cm规则：真实B的411格可通（右侧边界y=-0.325）；配准B网格凸包432格已无路（y=-0.375）；保存的体素占据467格亦无路。体素占据比配准网格凸包多35格；故封路已经发生在配准后的网格，不只是体素化。
- 未修改配准、场景、自检或规划方法。仍需负责人补充§0.3未覆盖的“准入但封路”处理规则；只解除网络依赖不能跳过完整替身链到达条件。
