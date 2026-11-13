# 先见一步 · BeforeStep

<!-- PHOTO-STORY-README-START -->
对轮子来说，石头是障碍，知道轮廓就能绕开；对腿来说，石头是地形，必须知道整块的形状。可整块石头有一半，机器人永远拍不到。BeforeStep 让 Lux3D 把那一半想象出来，再让轮腿机器人在迈步之前，把每一份想象都检验一遍、预演一遍。

[转着看真实生成的石头](https://codezzzsleep.github.io/next-zenith-beforestep/) · [想象陈列室](https://codezzzsleep.github.io/next-zenith-beforestep/gallery.html)。
<!-- PHOTO-STORY-README-END -->

## 三分钟跑起来 · Start in three minutes

克隆后拉取首页和完整锚点运行所需的 LFS 资产，再安装冻结依赖。以下一条零付费命令复用真实 Lux3D 资产，运行观测、自检、全部物理预演与独立执行，完成后打开本地作品页。三分钟是安装与启动目标；完整仿真耗时随设备变化，实际新目录用时见[执行记录](docs/reviews/RESULT_HACKATHON_AWARD.md)。不需要密钥。

Clone, fetch the LFS assets below, and install the frozen dependencies. The single zero-paid command reuses real Lux3D outputs, runs the full observation, checking, rehearsal and independent execution chain, then serves the local showcase. Three minutes is the setup/start target; full simulation timing is recorded in the [execution result](docs/reviews/RESULT_HACKATHON_AWARD.md). No API key is needed.

```bash
GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 https://github.com/codezzzsleep/next-zenith-beforestep.git
cd next-zenith-beforestep
git lfs install --local
git lfs pull --include="assets/runtime-*.tar.gz,assets/candidates/595*/tex_mesh.glb,evidence/reviews/beforestep_r1/lux/original_b/**,site/**,evidence/web-assets/**" --exclude=""
./setup.sh
.venv/bin/python ops/quickstart.py --reuse-lux --serve
```

Ubuntu/Debian 需先具备 Python 3.12 和 `venv`（缺少时：`sudo apt-get install python3.12-venv`）。

<!-- FRESH-TIMING-START -->
全新 GitHub 克隆实测：环境安装与启动 103.71 秒，完整零付费链另耗时 1287.87 秒；12 个世界完整预演、独立执行与五组轨迹数组核对均通过，新增任务 0。[原始实测记录](evidence/award/acceptance/C5-fresh.json)。网页在链完成后用同一全新环境独立启动并验收。

Fresh-clone verification: setup/start 103.71 s, followed by 1287.87 s for the full zero-paid chain. All 12 rehearsals and five trajectory-array comparisons passed. The local showcase was served independently after completion in the same environment.
<!-- FRESH-TIMING-END -->

打开 <http://127.0.0.1:8080>。全部其余历史证据可以另用 `git lfs pull --include="" --exclude=""` 下载。六步源文件、独立命令与输出见[代码导览](docs/code-tour.md)。

当前主线以 [负责人R1复核](docs/reviews/REVIEW_BEFORESTEP_R1.md) 为准：stress_v8 A+B、规则控制器与原终点(10.5,0)。[R1执行结果](docs/reviews/RESULT_BEFORESTEP_R1.md)逐项保留预期、原始结果与未完成项；以下v0.3与训练模型材料保留为历史交付和迭代附录。

面向轮腿机器人导航实验的盲区推演系统：用 **Aholo Lux3D** 生成受实际观测约束的候选几何，在物理仿真中检验路线，再决定前进、补充观察或停下。当前任务是在月球南极的岩壁、月溪和遮挡岩石之间完成通行。

由 Next Zenith 开发，参加 Aholo 黑客松。[项目目标与开发原则](docs/project.md)说明系统解决的问题、当前能力和后续验证方向。

Lux3D 是核心流程：真实观察图 → 原始生成 GLB → 配准与冻结自检 → 候选占据图 → 物理预演 → 独立真值执行。生成任务、输入摘要、被拒资产和完整终态均保留。

- [在线体验](https://codezzzsleep.github.io/next-zenith-beforestep/)
- [项目报告](docs/report.md) · [技术与资产迭代](docs/milestones.md)
- [历史 v0.3 Demo（R1新版由负责人制作）](site/media/demo.mp4) · [完整资产清单](assets/manifest.json)
- [交付结果与证据](evidence/delivery/)
- [训练模型与实际执行](site/learning.html) · [训练方法、权重和独立评估](docs/training.md)
- [随机环境中的新学习导航](site/navigation.html) · [首次留出结果、权重与复现](docs/learned-navigation.md)
- [主动观察控制的新训练与四眼通行](docs/observation-control.md) · [真实同观测对照视频](evidence/learning/observation_pose_v2/demo.mp4)

<!-- SUITE-README-START -->
## 预注册场景组实测

冻结 12 个场景，完整完成 12 个。决定性场景：到达 3、安全终止 3、碰撞 2；普通场景：到达 3/4。
全部拒绝候选反事实碰撞 17/102，另 0 份不能执行。真实第二眼 5 场。

**想象策略实际发生碰撞：suite_r2_v4_F1_020、suite_r2_v4_F3_004。候选自检和预演通过不能代替独立执行的安全结果。**

[五种策略完整总表与逐类边界](docs/suite.md) · [冻结名单](config/suite/frozen.json) · [原始汇总](evidence/suite/summary.json) · [运行与保全记录](docs/reviews/RESULT_BEFORESTEP_R2.md)。网页关卡回放已完成物理实验；沙盒是轻量几何规划，完整物理验证与实时云端生成在本地运行。
<!-- SUITE-README-END -->
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

## R1主线与核对

默认网页为stress_v8 A+B、rules：保守停车、see-dark对照到达、乐观碰撞，真实Lux一眼到达；完整重放一致，全部被拒B反事实0/3碰撞，自检偏保守。完整原始数据与失败见[evidence/reviews/beforestep_r1](evidence/reviews/beforestep_r1/README.md)。R1报告与网页数字可重复核对：

```bash
.venv/bin/python ops/verify_r1_evidence.py
.venv/bin/python ops/verify_r1_presentation.py
```

以下运行是保留的历史训练控制附录。冻结R1/R2/R3复现统一rules、不带pose-model，不触发新训练或新建Lux任务。2026-11-12新增的独立随机环境学习导航见[首次完整结果](docs/learned-navigation.md)。

## 历史复现实验

```bash
# 当前训练模型 + 实时观测 + 已保留的真实Lux资产；每次重新自检/规划/预演/执行。
MUJOCO_GL=egl .venv/bin/python -m beforestep run --scene gate_passage_001 --policy imagination --imagine lux \
  --goal 5.7 -.5 --reuse-lux assets/observations/trained_live_gate_001 --out outputs/reproduction_lux
# 同模型、同终点，去掉生成几何。
MUJOCO_GL=egl .venv/bin/python -m beforestep run --scene gate_passage_001 --policy optimistic \
  --goal 5.7 -.5 --out outputs/reproduction_reference
.venv/bin/python -m unittest discover -s tests -v
```

重新生成展示数据与对比图可运行 `beforestep build` 并传入三个策略运行目录；加 `--video` 会用 ffmpeg 输出真实轨迹视频，加 `--report` 输出 HTML 报告（先安装 `pip install -e '.[report]'`）。

运行默认使用已训练的v4控制模型。v0.2规则基线需显式 `--controller-model rules`，原终点8.5与观察集 `assets/observations/gate_passage_001` 保留。训练模型的部署与对照命令见[训练记录](docs/training.md)。主场景默认选择 gate_passage_001；历史压力案例使用 `--scene stress_v8 --controller-model rules --recorded-observations assets/observations/reference_v8`。

已完成的运行目录保留完整证据，再次实验请使用新的 `--out` 或 `--tag`；程序拒绝覆盖已有终态。尚在等待 Lux3D 结果的未完成运行可以在原目录恢复。

记录观测模式明确使用保留的真实 RGB-D 和 Lux3D 输入，并核对每次观察的机器人姿态、仿真时刻。它会重新配准、自检、规划和执行，不复用旧的规划结论。实时模式省略 `--recorded-observations`，`--reuse-lux` 只复用与新渲染输入逐字节相同的资产。跨渲染环境可加 `--start-at-recorded-look` 从记录状态开始，参见训练文档；需要生成时退出码为 `10`，请求落盘在输出目录的 `NEED_LUX3D.json`。

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

v0.3已完成实际模型训练和部署：v4使用115490真实示教、另计20000目标增强、BC30轮/PPO16384真实控制步，固定BC在新种子全角/近距16目标中完成15/16。网络控制运动，图规划和生成准入是独立模块。

新实时Lux输入六任务五份GLB成功、三候选通过冻结自检。主终点(5.7,-0.5)的生成几何改变路线，三候选完整无碰撞预演，独立执行一眼46.02s到达并复跑；原终点(8.5,0)也两次到达。同模型去掉生成几何46.66s也到达，不能宣称避免对照碰撞或端到端速度优势。主动观察姿态仍未通过，v5/v6失败与近岩石目标被候选封路的反例公开保留。

已发布v0.2.1与更早版本保持冻结；网页可切换规则控制原关口和旧双盲区压力反例。新的权重、数据、任务身份、独立记录与复现方法见[训练记录](docs/training.md)。

[第三方资产来源与许可证](docs/credits.md)。源码按完整参赛材料交付。
