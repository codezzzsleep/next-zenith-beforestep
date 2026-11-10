# RESULT_BEFORESTEP_R1

执行依据：[REVIEW_BEFORESTEP_R1.md](REVIEW_BEFORESTEP_R1.md)。主线为 `stress_v8`（A+B）、终点 `(10.5,0)`、规则控制器。冻结几何、太阳、传感器链、自检门槛、5 cm余量与两眼上限保持。本文在每次运行之前记录预期，之后保留原始终态并逐项对照。

## 提交与当前阶段

- `fdcf629`：按复核§7纳入训练控制附录与文献/同图审计；主线不使用训练控制或姿态模型。
- `7b6f5b4`：复核原文SHA256 `0541ef2d38d695e7b6efd044ef6c64ed47cf0b89b7fd4aff50725a7ea36eed29`，与附件逐字节一致。
- `73430ec`：§2.0预注册及stress_v8的purpose主展示标记；实际运行均以此源码启动。
- 当前阶段：§2.0四项已完成且按预期；准备§2.1–§2.3，没有新Lux3D付费任务。

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

尚未执行；每个新运行/付费批次在启动前于此登记。第二眼B输入不足时仍按§2.2单图6份，0采纳仅追加同字节一批6份；合计12份仍0安全停车并进入预注册§2.4。没有新增场景、放宽门槛或第三眼的授权。

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
