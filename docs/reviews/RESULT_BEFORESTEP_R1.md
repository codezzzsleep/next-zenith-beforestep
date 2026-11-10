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
