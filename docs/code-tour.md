# 五分钟代码导览

一张真实照片经 Lux3D 变成完整石头候选；原始几何直接进入检查、占据与物理预演。月面太阳与遮挡提供实验背景，真实模型生成承担核心作用。源码冻结在 `4d53214`，下列只读审计和运行入口在 `ops/`，没有改动实验方法。

先按 README 安装依赖。所有路径相对仓库根；以下默认复用资产且零新增付费。`outputs/` 中的运行记录不会覆盖原证据。

| 步骤 | 作用与代码入口 | 能单独运行的命令 | 输出 |
| --- | --- | --- | --- |
| 观察 | [`capture.py`](../src/beforestep/observation/capture.py) `capture` 记录 RGB、depth、DARK，并用实际视线提取目标；[`images.py`](../src/beforestep/observation/images.py) `_variants` 准备真实上传图。 | `.venv/bin/python -m beforestep run --scene stress_v8 --controller-model rules --policy conservative --out outputs/tour-observe` | `outputs/tour-observe/conservative/looks/look1/T*/` 的 `rgb.png`、`depth.npy`、`state.json`、`gen/variants/`；此命令还完成保守基线。 |
| 生成 | [`records.py`](../src/beforestep/generation/records.py) `write_request` 固定图片与身份；[`client.py`](../src/beforestep/generation/client.py) `submit`、`poll` 返回原始 GLB，`read_result` 逐 SHA 验证其来源。 | `.venv/bin/python ops/check_candidate.py --run evidence/reviews/beforestep_r1/lux/original_b --target T2 --sample A2` | 终端显示真实任务、原 GLB/决策 SHA 与测量值；原生成文件是 `assets/candidates/5958654/tex_mesh.glb`。这条安全命令核对既有生成来源，不重新调用服务。 |
| 检查 | [`imagination.py`](../src/beforestep/geometry/imagination.py) `decide_target` 完成配准、体素指标与导航占地；[`admission.py`](../src/beforestep/geometry/admission.py) `admitted` 只用冻结门槛。 | `.venv/bin/python ops/check_candidate.py --run evidence/reviews/beforestep_r1/lux/original_b --target T2 --sample C1` | stdout：各项原测量、冻结上下限、五个门卫布尔值与生产结论。这里只重算门卫，不重新测量几何。 |
| 预演 | [`pipeline.py`](../src/beforestep/pipeline.py) `main` 内的 `rehearse` 和 [`imagination.py`](../src/beforestep/geometry/imagination.py) `rehearsal_spec` 将每个采纳候选世界交给同一机器人和控制器完整行走。 | `.venv/bin/python ops/quickstart.py --reuse-lux --out outputs/tour-chain` | `outputs/tour-chain/run/imagination/rehearsal/look1/pane*/traj.npz`、`events.jsonl`；同一命令也完成独立执行，保证没有绕过预演。 |
| 执行 | [`pipeline.py`](../src/beforestep/pipeline.py) `main`、[`controller.py`](../src/beforestep/navigation/controller.py) `run_waypoints` 在独立真实环境执行路线；[`controller.py`](../src/beforestep/navigation/controller.py) `drive_to` / `turn_to` 控制动作。 | `.venv/bin/python ops/quickstart.py --reuse-lux --out outputs/tour-execution` | `outputs/tour-execution/run/imagination/traj.npz`、`summary.json`、`run_identity.json`；生产方法每次都先检查和预演。 |
| 复盘 | [`evaluation.py`](../src/beforestep/evaluation.py) `main`、`truth_footprints` 对照执行后真值；[`r3_video_review.py`](../ops/r3_video_review.py) 复核接触和三维距离。 | `.venv/bin/python ops/r3_video_review.py --run evidence/reviews/beforestep_r1/lux/original_b --need-xy` | `outputs/video/r3/reviews/<run_id>/eval.json`：独立只读复盘副本的逐眼想象占地与真值对照；真值诊断永远不作为生成或生产输入。 |

完整默认流程是一条 `ops/quickstart.py --reuse-lux`。若要查看真实在线生成接口，运行 `.venv/bin/python -m beforestep generate --help`；这个帮助命令零付费。服务创建只在单独授权、预算账本与实际上传身份门卫满足后执行，代码位置是 `client.py::submit`，不是网页模型查看器。

候选检查通过不代表背面正确：F1_020 没有观测到 C；F3_004、F0_003、F3_006 的 B 背面被低估。它们始终保留在[技术报告](../site/report.html)和[原始结果](reviews/RESULT_HACKATHON_AWARD.md)。
