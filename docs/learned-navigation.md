# 学习导航实验

用户要求增加实际训练的导航模型，并以随机环境中的新任务验证泛化。
本实验独立于已冻结的 R1/R2/R3。训练和测试协议见
[预注册协议](learned-navigation-protocol.md)，固定参数见
[navigation_v1.json](../config/training/navigation_v1.json)。

## 可运行的实现

```bash
python3 -m venv .venv-nav
.venv-nav/bin/pip install -r requirements.txt -r requirements-navigation.txt
PYTHONPATH=src .venv-nav/bin/python ops/learned_navigation.py library

# 任意新种子生成环境；同时输出可编译的 MuJoCo 场景。
PYTHONPATH=src MUJOCO_GL=egl .venv-nav/bin/python ops/learned_navigation.py generate \
  --seed 7200123 --distribution ood --mujoco --out outputs/navigation-new-world

# 实际训练，已有输出只能显式续训，不能覆盖。
PYTHONPATH=src .venv-nav/bin/python ops/learned_navigation.py train \
  --out outputs/learning/navigation-new
PYTHONPATH=src .venv-nav/bin/python ops/learned_navigation.py train \
  --out outputs/learning/navigation-new --resume

# 固定权重后的新种子对照：二维导航与物理执行分别记结果。
PYTHONPATH=src .venv-nav/bin/python ops/learned_navigation.py evaluate \
  --training outputs/learning/navigation-new --out outputs/navigation-test-new
PYTHONPATH=src MUJOCO_GL=egl .venv-nav/bin/python ops/learned_navigation.py physics \
  --training outputs/learning/navigation-new --out outputs/navigation-physics-new
```

MuJoCo 凸包挤出体使用扫描俯视形状作为基底；传感器目前仍是二维视线与阴影模型。
它能验证机器人动作、物理接触和目标到达，完整生产 RGB-D/Lux3D 实时闭环是另一项
验收，不能将这两者混称。新环境只迁移真实已存 Lux3D 先验，云端新增任务为零。

## 各层能力

| 层次 | 新实验实现 | 学习状态 |
| --- | --- | --- |
| 石头几何先验 | 真实已存 Lux3D 几何共同随机迁移 | 不重新训练 Lux3D |
| 地图中的可通行性 | 4输入通道的卷积网络 | 实际监督训练 |
| 朝向目标的下一移动方向 | 神经价值迭代八方向得分 | 代价与卷积参数训练，固定八邻域拓扑 |
| 观测更新和已见障碍门卫 | 明确的几何规则 | 未训练 |
| 轮速、转向、腿部残差 | 既有 v4 目标控制网络 | 历史实际训练权重，所有物理对照共用 |

模型在新布局中的性能必须由完整留出结果决定，不能仅凭存在权重文件声称可靠泛化。

## 规则加大语言模型

接口参考 [Agentic Observer](https://github.com/codezzzsleep/gosim26-agentic-observer) 的
数值证据与结构化模型判断设计，本项目独立实现。规则计算候选动作和可见性/估计
距离，模型选择候选、观察或停车。每次请求在发送前保存身份和上下文，输出经过
候选身份校验；API 错误和预算耗尽单列，规则回退不能计作模型动作。

在私有文件设置 `NAV_LLM_API_KEY`、`NAV_LLM_BASE_URL`（兼容服务的 v1 地址）和
`NAV_LLM_MODEL`，然后运行：

```bash
PYTHONPATH=src .venv-nav/bin/python ops/learned_navigation.py llm \
  --env-file /private/path/model.env --max-calls 32 \
  --out outputs/navigation-llm-new
```

默认 LLM 比较使用另一区间 6100000 起的8个种子，最多32次请求。
若继续独立对照，必须用 `--prior-calls outputs/navigation-llm-new/calls` 计入
此前已发送请求；禁止换目录重置额度。没有实际模型答复时，回退结果单列。
