# 机器人模型训练与独立任务评估

新增的可选朝向控制训练、同输入四眼到达与失败保留见[主动观察控制](observation-control.md)。它复用 v4 运动底座，独立训练两输入的终端朝向网络；冻结 v0.3 模型与实验仍按本文原记录保留。

BeforeStep 使用实际训练得到的神经网络控制机器人运动。网络读取本体状态、目标在机器人坐标系中的位置和上一动作，输出前后腿姿态残差、前进轮速和差速转向。推理不调用示教专家或规则导航底座；PD 伺服负责把网络动作下发到关节和轮子。图规划、Lux3D 几何准入与候选选择是独立、明确的系统模块。

训练和执行都通过 MuJoCo 的真实动力学步推进，月面重力为 1.62m/s²。初始化或恢复实验状态发生在轨迹开始之前；运行中不把脚本位置写进机器人状态来替代动作执行。网页和视频回放保存的实际轨迹。

## 模型迭代

| 版本 | 实际训练与问题 | 证据 |
| --- | --- | --- |
| v1 | 64个物理示教回合、57584个状态动作，BC与65536步PPO；BC目标13/16，但月面关口越过路点后转向碰撞；最终PPO目标0/16 | `outputs/training/goal_controller_001` 为原运行；[原训练与代表失败](../evidence/training/goal_controller_v1/manifest.json) |
| v2 | 49维目标编码，20cm尺度近目标坐标；复用57584个真实示教，加20000个明确标注的反事实目标监督样本；BC、PPO与独立评估实际运行 | [冻结权重与来源](../evidence/training/goal_controller_v2/manifest.json) |
| 完整复跑 | 保留v2中断作业，另起运行完成65536个真实PPO控制步；最终模型在原16个验证目标上完成16/16 | [完整训练摘要](../evidence/training/goal_controller_v3_reproduction/summary.json) |
| v4（正式部署） | 新增64回合57906真实示教，与旧57584行合并；BC30轮与16384真实PPO步。固定BC在新种子全角/近距完成15/16，并完成实时Lux主任务与独立复跑 | [冻结权重与完整训练](../evidence/training/goal_controller_v4/manifest.json) |
| v5 | 扩大终端目标监督，复用115490物理示教、50000另计目标增强、BC15轮/PPO8192步；原验证BC14/16、PPO16/16，月面主动观察姿态仍失败 | [训练与权重](../evidence/training/goal_controller_v5/manifest.json) |
| v6 | 51维合同显式区分已完成平移与剩余朝向；BC15轮/PPO8192步，原验证16/16，但主动观察及姿态分步实验仍失败。未替换v4 | [训练与权重](../evidence/training/goal_controller_v6/manifest.json) |

v2原作业在49152步后退出137，退出原因未确认。已冻结BC、u16最佳验证权重、u48未验证权重和与启动摘要一致的源码；不把中断运行写成训练完成。完整复跑有自己的身份和源码快照。

v1启动摘要所列47个源码文件中，保存了46个；当时的pipeline.py没有快照，清单明确列出，不能声称完整保存。后续v2/v4/v5/v6的源码快照按启动SHA核验。

原始物理示教和监督目标增强分开记录。20000个增强行改变目标标签，不是新增物理动力学步。v4暖启动沿用已有网络权重，新的优化器、示教与物理采样另有运行身份，不能冒充恢复了旧作业。

## 新种子公平评估

模型选择使用900001起的验证目标；下表的新测试目标使用不同种子。每组模型得到相同目标、初始姿态、月面动力学和65秒时限。完成要求是位置误差小于75mm、明确指定时的朝向误差小于4°，并连续5个控制帧停稳。场景任务没有指定最终朝向时，不以最终朝向数值宣称通过4°测试。

| 新测试组 | PPO v2 | BC v2 | 未训练 | 规则专家 |
| --- | --- | --- | --- | --- |
| 平地32目标，种子940001起 | 28/32 | 23/32 | 0/32 | 32/32 |
| 2°坡度、4mm粗糙度，16目标，种子950001起 | 14/16 | 未运行 | 未运行 | 11/16 |

这些结果证明训练后的网络学到了可用动作；平地对照中规则专家的成功率更高，坡地样本也不足以推出普遍优势。所有失败回合和误差都保留，不能只挑成功目标汇报。

[平地完整清单](../evidence/learning/held_out_v2_flat/summary.json) · [坡地完整清单](../evidence/learning/held_out_v2_slope/summary.json) · [交互查看](../site/learning.html)

## 月面任务与真实 Lux3D

固定PPO v2在双岩石任务从原场景起点实际运行，一眼69.16s到达、无碰撞。该次实时观测没有使用生成几何，不能算作Lux3D收益；旧规则在同场景碰撞是另一控制器的结果，不能混为只移除生成几何的公平对照。

固定PPO v2与真实Lux3D资产连接的关口实验两次完成：三份真实采纳候选分别完整预演、无碰撞，随后在独立扫描真值环境实际到达。实验从保留的观测状态开始，机器人完整姿态、速度、观测字节和仿真时刻均校验；执行elapsed为37.36s，终点位置误差约51mm。原场景起点到观察点的运动没有被写成这次模型执行。云端资产来自真实已保存任务，未冒充本次联网生成。

将同一物理场景的任务终点显式改为(5.4,-0.7)，同一观测、模型与规划器下，加入生成几何改变了路线；扫描几何估计的直行余量从51mm变为117mm，仅作设计/执行后的诊断。v2模型不能完成选定路线的最后短距离转向，三份预演均超时，系统正确拒绝执行。这是模型分布覆盖不足的失败，随后以一般的全角和近目标物理示教改进，不能把这次停下当作任务成功。参照路线本身可以到达，未人为制造对照碰撞。


| 新测试组 | BC v4 | PPO v2 | 规则专家 |
| --- | --- | --- | --- |
| 全角/近目标16任务，种子970001起 | 15/16 | 10/16 | 16/16 |

[完整任务与失败清单](../evidence/learning/held_out_v4/summary.json)。模型选择使用原900001起目标，新测试不参与训练或权重选择。规则对照仍更可靠；网络已学到可用运动，不表示通用能力超过规则。

## v4实时Lux闭环与同模型对照

正式部署权重为 `assets/models/goal_controller_v4/behavior_cloning.npz`，其SHA256为 `bd6ca91b73c400ebbfdaed4258f6e2eb20d769468b0d01eba910d16a36f4f970`。模型从场景原起点实际运动，实时RGB-D产生新输入，经真实云端生成、自检和候选预演，再在独立扫描几何物理环境执行。

| 任务 | Lux分支 | 同模型去掉生成 | 其他结果 |
| --- | --- | --- | --- |
| 原终点(8.5,0) | 两次1眼54.02s执行行程到达，每次3/3预演完成/无碰撞 | v4实测54.02s到达 | 历史v0.2规则对照单独保留 |
| 主终点(5.7,-0.5) | 两次1眼46.02s到达，参照与选定路线各3/3预演通过 | 1眼46.66s到达 | 同模型保守观察3次观察点尝试未达姿态，283.44s未完成 |
| 近岩石(5.4,-0.7) | 采纳候选的占据封住路线，1眼15.42s停止 | 1眼45.00s到达 | 候选过于保守的负例，不能视为任务成功 |

以上行程从真实轨迹起点计算；主Lux任务总仿真时间47.22s含1.20s初始化停稳，云端生成/配准不包括在行程时间里。三种主任务对照的首次RGB-D/地图SHA、模型、场景和目标一致。生成加入后路线改变，扫描诊断直行余量82→120mm，真值没有输入规划器。去掉生成也到达，不能宣称避免了碰撞或端到端速度优势。

[新实时输入与六任务身份](../experiments/trained_live_gate_001/manifest.json) · [独立链与公平性核验](../evidence/scenes/trained_live_gate_001/validation.json) · [20个真实任务交互回放](../site/learning.html)

主动观察失败是尚未解决的模型控制限制：转向时的位置漂移与近点朝向冲突会使机器人达不到原75mm/4°停稳门槛。v5/v6新训练和v6分步实验均保留实际失败，没有降低阈值或用规则控制补做成功。

## 复现训练与部署

安装和资源恢复见 [README](../README.md)。NumPy实现可在CPU上训练；本仓库包含训练代码、冻结模型、真实物理示教、关键源码快照和结果。运行输出使用独立目录，完成的结果不能覆盖。

```bash
# 正式模型：从原场景起点重新渲染观测、检查保存资产、预演并执行。
# 同渲染环境下逐字节核对；输入不符会拒绝复用，不新建付费任务。
MUJOCO_GL=egl .venv/bin/python -m beforestep run --scene gate_passage_001 \
  --policy imagination --imagine lux --goal 5.7 -.5 \
  --reuse-lux assets/observations/trained_live_gate_001 --out outputs/trained_live_new

# 同模型与同终点，去掉生成几何。输出目录必须独立。
MUJOCO_GL=egl .venv/bin/python -m beforestep run --scene gate_passage_001 \
  --policy optimistic --goal 5.7 -.5 --out outputs/trained_reference_new

# 跨渲染环境复现：明确从记录观测状态开始，不把前段运动计入本次执行。
MUJOCO_GL=egl .venv/bin/python -m beforestep run --scene gate_passage_001 \
  --policy imagination --imagine lux --goal 5.7 -.5 \
  --recorded-observations assets/observations/trained_live_gate_001 \
  --start-at-recorded-look --max-looks 1 --out outputs/trained_recorded_new

# 新种子公平评估固定模型；测试目标与训练、模型选择分开。
MUJOCO_GL=egl .venv/bin/python -m beforestep evaluate-controller \
  --model v4=assets/models/goal_controller_v4/behavior_cloning.npz \
  --model v2=assets/models/goal_controller_v2/ppo_u0016.npz --model rules=rules \
  --task-config config/training/goal_controller_v4.json \
  --seed-start 980001 --episodes 16 --out outputs/controller_test_new

# 新训练身份，使用保留的真实示教和明确暖启动。
MUJOCO_GL=egl .venv/bin/python -m beforestep train --config config/training/goal_controller_v4.json \
  --demonstrations-from assets/training/goal_controller_v4 \
  --initial-checkpoint assets/models/goal_controller_v2/ppo_u0016.npz \
  --out outputs/controller_training_new
```

新的训练按更新边界原子保存网络、Adam动量、随机流、MuJoCo状态、当前任务和累计步数。恢复使用相同训练配置和依赖源码：

```bash
MUJOCO_GL=egl .venv/bin/python -m beforestep train --config config/training/goal_controller_v4.json \
  --out outputs/controller_training_new --resume
```

旧v2只有模型权重，无法原样恢复优化器与物理采样；完整状态机制适用于新运行。实际短程验证将32个连续训练步与16步中断后续训比较，最终所有网络参数差为0；该测试验证恢复机制，不算机器人任务成果。
