# 先见一步 · BeforeStep

面向轮腿机器人导航实验的盲区推演系统：用 **Aholo Lux3D** 生成受实际观测约束的候选几何，在物理仿真中检验路线，再决定前进、补充观察或停下。当前任务是在月球南极的岩壁、月溪和遮挡岩石之间完成通行。

由 Next Zenith 开发，参加 Aholo 黑客松。[项目目标与开发原则](docs/project.md)说明系统解决的问题、当前能力和后续验证方向。

Lux3D 是核心流程：真实观察图 → 原始生成 GLB → 配准与冻结自检 → 候选占据图 → 物理预演 → 独立真值执行。生成任务、输入摘要、被拒资产和完整终态均保留。

- [在线体验](https://codezzzsleep.github.io/next-zenith-beforestep/)
- [项目报告](docs/report.md) · [技术与资产迭代](docs/milestones.md)
- [真实 Demo 视频](site/media/demo.mp4) · [完整资产清单](assets/manifest.json)
- [交付结果与证据](evidence/delivery/)

## 运行

需要 Python 3.12、Git LFS；Linux 离屏仿真需要 EGL 或 OSMesa。观看本地作品页无需 Lux3D 密钥或新增付费调用。

```bash
git clone https://github.com/codezzzsleep/next-zenith-beforestep.git
cd next-zenith-beforestep
git lfs pull
./setup.sh
.venv/bin/python -m beforestep serve
```

打开 <http://127.0.0.1:8080>：切换三个策略，回放真实轨迹，旋转真实生成的 3D 资产，查看迭代与视频。

离屏渲染默认使用 `MUJOCO_GL=egl`。如机器仅支持 OSMesa，可用 `MUJOCO_GL=osmesa ./setup.sh`。机器人与所需岩石已打包在本仓库，按摘要校验恢复；不依赖旧仓库的运行目录或缓存。

Release 中的完整源码 ZIP 含实体资产，解压后可直接 `./setup.sh`，无需 Git LFS 下载。

## 复现实验

```bash
MUJOCO_GL=egl .venv/bin/python -m beforestep run --scene gate_passage_001 --policy conservative --out outputs/reproduction
MUJOCO_GL=egl .venv/bin/python -m beforestep run --scene gate_passage_001 --policy optimistic --out outputs/reproduction
MUJOCO_GL=egl .venv/bin/python -m beforestep run --scene gate_passage_001 --policy imagination --imagine lux \
  --recorded-observations assets/observations/gate_passage_001 --out outputs/reproduction
.venv/bin/python -m unittest discover -s tests -v
```

重新生成展示数据与对比图可运行 `beforestep build` 并传入三个策略运行目录；加 `--video` 会用 ffmpeg 输出真实轨迹视频，加 `--report` 输出 HTML 报告（先安装 `pip install -e '.[report]'`）。

主场景可复现实验默认选择 gate_passage_001；历史压力案例使用 `--scene stress_v8 --recorded-observations assets/observations/reference_v8`。

已完成的运行目录保留完整证据，再次实验请使用新的 `--out` 或 `--tag`；程序拒绝覆盖已有终态。尚在等待 Lux3D 结果的未完成运行可以在原目录恢复。

记录观测模式明确使用保留的真实 RGB-D 和 Lux3D 输入，并核对每次观察的机器人姿态、仿真时刻。它会重新配准、自检、规划和执行，不复用旧的规划结论。实时模式省略 `--recorded-observations`；需要生成时退出码为 `10`，请求落盘在输出目录的 `NEED_LUX3D.json`。

新增生成使用环境变量 `AHOLO_API_KEY`，或 `--env-file` 指向仓库外的密钥文件（支持 `API_key` 字段）。创建任务需明确传入 `--submit`；同一请求恢复查询时不传此参数。

```bash
.venv/bin/python -m beforestep generate --request <请求文件> --env-file <仓库外.env> --submit --wait
.venv/bin/python -m beforestep generate --request <请求文件> --env-file <仓库外.env> --wait
```

创建响应不确定时保留 `uncertain` 状态并停止重复创建；任务 ID 一经收到立即落盘。输入相同、样本编号不同表示独立采样。实验 `polar_retry_001` 保留了新增两图生成的原始任务与输入变换说明。

## 仓库结构

| 目录 | 用途 |
| --- | --- |
| `src/beforestep` | 当前实现，按仿真、观测、几何、导航、生成、可视化、交付职责组织 |
| `config` | 冻结门槛、配准协议与自带运行资源摘要 |
| `assets` | 原始生成资产、输入与观测、关键迭代几何、运行资源 |
| `evidence/milestones` | V6/V7/V8 精选源码快照、配置、结果与局限 |
| `evidence/delivery` | 当前版本真实运行轨迹、终态与身份 |
| `experiments` | 有身份、有来源的新生成实验 |
| `site` | 可体验作品页、对比图与真实视频 |
| `docs` | 报告、迭代解释与交付决策 |
| `tests` | 当前实现的核心行为回归 |

运行产生的缓存、任务私有上传信息、临时输出写入忽略的 `outputs/`；不作为展示证据。关键结果经整理进入 `evidence/`。

## 结果边界

默认主场景 gate_passage_001 已完成真实 Lux3D 通行：六个新任务、四个成功 GLB、三个候选通过冻结自检，三个实际预演均完成/无碰撞，机器人一眼到达76.50s。保守同场景三眼118.76s到达，直接走也能一眼到达。旧双盲区 stress_v8 继续保留为失败/压力案例，不能用旧结果或真值替身冒充新场景成果。

[第三方资产来源与许可证](docs/credits.md)。源码按完整参赛材料交付。
