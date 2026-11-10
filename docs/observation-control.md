# 主动观察的训练控制与实测

可选的朝向网络 v2 已在关口任务中完成主动补充观察，再由 v4 运动网络到达终点。完整实时仿真两次得到相同结果：4 眼、302.22 秒执行行程、无碰撞。原默认 v4 联合目标控制和发布版 v0.3 保持可用；新能力通过 `--pose-model` 显式开启。

[真实同观测对照视频](../evidence/learning/observation_pose_v2/demo.mp4) · [轨迹与采集姿态图](../evidence/learning/observation_pose_v2/comparison.png) · [逐项核验](../evidence/learning/observation_pose_v2/validation.json)

## 实际改动

原 v4 在观察点附近常减速到距离目标约 5–6cm，剩余位置目标与朝向目标相互干扰。新控制让 v4 先闭合位置，再用独立训练的朝向网络转向。平移时使用沿目标方向延伸 4cm 的控制子目标；进入原观察点 25mm 内且线速度低于 35mm/s 后交接，漂移到 60mm 时重新校正位置。原规划目标和最终请求姿态始终不变。

朝向网络读取相对朝向误差和实测角速度，经过两层 32 单元网络输出四维电机动作向量。其腿部残差与前进通道为训练的零动作，差速转向通道产生运动。v4 与朝向网络的动作通过既有 PD 伺服执行，导航底座关闭。控制交接和图规划是明确的独立模块。

原完成条件仍为 75mm、指定朝向误差小于 4°、线速度小于 35mm/s、角速度小于 0.08rad/s，连续 5 个控制帧满足要求。新朝向控制使用更严格的 3°内部停稳目标，为停车后采集时的小幅漂移留余量。最终两份实验的六个补充采集点实测位置误差为 16.6–55.8mm，朝向为 2.72–2.99°，线速度最高 1.38mm/s，均通过原门槛。

## 真实训练与版本保留

姿态头 v1 新采集了 64 个 MuJoCo 物理回合，共 24,448 个状态动作记录、282,880 个物理步；另有 24,448 个镜像监督行，完成 40 轮行为克隆。它能在一般目标测试中通过，但完整观察任务仍有失败，小角度转向量偏低。

姿态头 v2 复用这批真实示教，新增 20,000 个明确单列的小角度反事实目标监督行，对 2–10°样本加权；镜像监督共 44,448 行，完成 80 轮行为克隆。本次补训新增物理行数为 0，没有新增 PPO 采样。3°、零角速度时的网络差速输出从 v1 的 0.466rad/s 提高到 v2 的 0.910rad/s；真正的任务效果由后面的独立执行检验。

正式可选权重是 [pose.npz](../assets/models/observation_pose_v2/pose.npz)，SHA256 为 `dc48b6404a6c0118e1ef82fd89b42a07bd7953bfb625e5ed60a6ed945e36f5da`。

[原物理示教](../assets/training/observation_pose_v1/demonstrations.npz)、[v1 启动源码与曲线](../evidence/training/observation_pose_v1/manifest.json)、[v2 启动源码与曲线](../evidence/training/observation_pose_v2/manifest.json)、[训练与小角度动作图](../evidence/learning/observation_pose_v2/training.png)均保留。历史初版到达但采集朝向处于门槛边缘、严格余量失败、位置校正失败及停稳交接前的实时失败，分别保留在[版本与回放清单](../evidence/learning/observation_pose_v2/replays.json)；这些不算最终成功验收。

## 同条件任务结果

任务终点均为 `(5.7, -0.5)`，月面重力 1.62m/s²。

| 实验 | 实际结果 | 范围 |
| --- | --- | --- |
| v4 + 姿态头 v2，完整实时场景起点 | 两次 4 眼到达，302.22s，无碰撞 | 全部观测为当次实时仿真采集 |
| v4 + 姿态头 v2，从首次记录观测状态开始 | 两次 4 眼到达，205.18s，无碰撞 | 首眼为记录 RGB-D，后三眼为当次实时采集；不含前接近段 |
| 原 v4 联合目标控制，相同首次记录状态 | 1 眼，270.02s，观察姿态未完成 | 同源码、同场景、同基座模型、同首次 RGB-D/地图 |
| 装载可选姿态头的 Lux3D 兼容复跑 | 1 眼，32.60s 到达，六份物理预演完成/无碰撞 | 原真实生成资产、准确匹配的保留几何缓存；当前代码重新预演与执行 |

Lux 兼容路线没有终端朝向命令，姿态头未调用；该结果用于验证既有生成闭环的兼容性，不是新增云端生成或姿态头贡献证明。几何缓存身份仍为 `0127c83bdf403e44d6a36580bd773c10e9cddc396def70caf388b52b1e21b7e1`，原准入与协议保持不变。

最终源代码另以 160001 起的 8 个独立姿态任务评估：原 v4、新组合、规则专家均 8/8，平均位置误差分别 41.3、24.2、50.3mm。[完整清单](../evidence/learning/pose_v2_final_held_out/summary.json)与每回合结果保留。此前 140001 起的 v1 测试和 150001 起的 v2 测试也分别保留，不能合并为最终源代码的同一批验证。

这些对照评估的是训练姿态头与交接机制的整体效果。当前只验证了该关口和小规模姿态任务，观察点仍会超时重试，完整实时行程仍长，尚未证明普遍安全或速度优势。保留默认入口还确保既有实时 Lux 输入身份可以复用：启用新的接近控制会产生不同截图，需要独立匹配生成输入。

## 运行与复现

先按 [README](../README.md)恢复 LFS 与运行资源，输出目录使用新的名称。

```bash
# 从实际场景起点开始，开启训练姿态控制。
MUJOCO_GL=egl .venv/bin/python -m beforestep run --scene gate_passage_001 \
  --policy conservative --goal 5.7 -.5 \
  --pose-model assets/models/observation_pose_v2/pose.npz --out outputs/pose_live_new

# 公平复现：首眼为相同记录状态，后续观测仍实时采集。
MUJOCO_GL=egl .venv/bin/python -m beforestep run --scene gate_passage_001 \
  --policy conservative --goal 5.7 -.5 \
  --pose-model assets/models/observation_pose_v2/pose.npz \
  --recorded-observations assets/observations/trained_live_gate_001 \
  --start-at-recorded-look --out outputs/pose_recorded_new

# 原 v4 对照使用上述相同命令，省略 --pose-model，另选输出目录。

# 从保留示教重新训练姿态头；本命令是新 BC 运行，没有旧 Adam 续训。
MUJOCO_GL=egl .venv/bin/python -m beforestep.learning.pose_train \
  --demonstrations-from assets/training/observation_pose_v1 \
  --goal-augmentation 20000 --near-yaw-weight 8 --epochs 80 --seed 131001 \
  --out outputs/pose_training_new
```

实际输入按原文件字节存入[完整实时输入包](../assets/observations/pose_v2_live/sensors.tar.gz)与[首眼记录任务输入包](../assets/observations/pose_v2_recorded/sensors.tar.gz)，各包的 `manifest.json` 保存成员 SHA256；PNG 同时提供预览。源码、模型、输入、失败、实际轨迹与核验均在本仓库内。冻结 v0.3 报告、视频、标签与发布附件不改变。
