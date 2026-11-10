# RESULT_BEFORESTEP_R1

执行依据：[REVIEW_BEFORESTEP_R1.md](REVIEW_BEFORESTEP_R1.md)。主线为 `stress_v8`（A+B）、终点 `(10.5,0)`、规则控制器。冻结几何、太阳、传感器链、自检门槛、5 cm余量与两眼上限保持。本文在每次运行之前记录预期，之后保留原始终态并逐项对照。

## 提交与当前阶段

- `fdcf629`：按复核§7纳入训练控制附录与文献/同图审计；主线不使用训练控制或姿态模型。
- 复核原文已逐字节复制并提交；提交号在后续检查点补记。
- 当前阶段：§2.0，尚未运行；没有新Lux3D付费任务。

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
