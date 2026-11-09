# 有效关口的独立运行证据

两次运行使用同一生产协议、真实 Lux3D 资产和实时观测，都一眼到达，三份候选预演均完成且无碰撞。`validation.json` 逐项指向各自原始事件流及 SHA256；末行是该次实际终态：

| 运行 | 原始事件流 | 仿真行程 | 本次计算墙钟时间 |
| --- | --- | --- | --- |
| 首次生产 | `trials/production.jsonl` | 76.50s | 78.2s |
| 同协议复跑 | `trials/repeat.jsonl` | 76.50s | 83.2s |

墙钟时间是已有生成资产与身份缓存的运行耗时，不包含先前云端生成和冷配准成本。

`imagination/`、主页面和视频使用第二次运行的完整轨迹、预演轨迹及运行身份。首次完整轨迹在复用同一输出目录时被覆盖，现存首次原始事件流独立保留；不声称保有两份独立的完整轨迹。早期整理产生的重复 `repeat/imagination/` 副本已去除，v0.2.0 标签保留原版本。

`conservative/` 和 `optimistic/` 是同场景真实对照；`admission/` 保存所有成功生成样本的自检、配准和候选占据。生成输入、四份原 GLB 和两次失败任务见 `assets/observations/gate_passage_001`、`assets/candidates`、`experiments/gate_passage_001`。
