<div align="center">

# 先见一步 · BeforeStep

**基于 Aholo Lux3D 局部空间先验与 MuJoCo 多世界物理预演的轮腿机器人导航系统**

[在线四站试玩](https://codezzzsleep.github.io/next-zenith-beforestep/play.html) · [作品首页](https://codezzzsleep.github.io/next-zenith-beforestep/) · [项目报告 V5 Beta](https://codezzzsleep.github.io/next-zenith-beforestep/report.html) · [宣传视频](https://www.bilibili.com/video/BV1YZst6eEZk/)

<a href="https://www.bilibili.com/video/BV1YZst6eEZk/">
  <img src="docs/readme/m20-bright-20261119/photo-to-model.gif" width="900" alt="M20 轮腿机器人观察岩石，原照片对应 Lux3D 三维模型">
</a>

</div>

---

## 一、问题与系统架构

在月球南极 **10° 低角度斜阳与岩石遮挡**的仿真场景中，机器人只能观测到障碍物朝向相机的一部分，被遮挡的背面几何仍是未知的。仅按可见表面规划可能撞上隐藏岩石，将阴影与未知区域全部视作阻塞则可能在窄道停滞。同时，在已测试的 **10、12、15 cm 三个离散低门槛高度**上，轮行未能通过，轮腿复合跨越提供了另一种执行能力。

**BeforeStep** 将单物体图生 3D 模型 [Aholo Lux3D](https://labs.aholo.ai/api-docs/specifications/services/lux3d/openapi.en.json) 的三维几何先验，接入机器人局部空间建模与物理预演闭环，作为机器人的 **“空间前额叶”**。根据[群核科技官方发布稿](https://www.prnewswire.com/news-releases/manycore-tech-unveils-lux3d-and-an-explicit-3d-path-to-world-models-302861778.html)，Lux3D 结合生成数据与物理世界重建数据训练，以改善几何与视觉一致性；在本系统中，候选网格提供空间假设，MuJoCo 计算运动与接触后果。

1. **二维观测与局部想象**：从普通 RGB 图像提取被遮挡岩石，调用 Lux3D 生成多份完整 3D 候选网格。深度不是 API 上传要求，已有 RGB-D、位姿和地形用于本地尺度恢复、配准与核对。
2. **观测核对与空间配准**：将候选网格与可见表面尺度、轮廓逐一核对，剔除不符合观测约束的候选，再把采纳几何放回通道坐标系计算障碍占据。
3. **多世界物理预演**：原 R1 的六份 A × 两份 B 构成 **12 个候选世界**，逐世界完整预演。辅助路线通过当前所选全部世界的预演后才可执行；信息不足时支持停车或补看。
4. **轮腿分级执行**：高大遮挡石依靠局部空间假设支持绕行，清晰可见的低门槛使用轮腿跨越；玩家逐腿执行抬起、前移、落地，控制器辅助支撑与平衡。

<picture>
  <source media="(max-width: 600px)" srcset="docs/assets/forebrain-pipeline-mobile.svg">
  <img src="docs/assets/forebrain-pipeline.svg" alt="BeforeStep 空间前额叶五步闭环架构" width="100%">
</picture>

<picture>
  <source media="(max-width: 600px)" srcset="docs/readme/m20-bright-20261119/model-action-mobile.jpg">
  <img src="docs/readme/m20-bright-20261119/model-action-desktop.jpg" width="100%" alt="Lux3D 原模型与 M20 探索行动对照">
</picture>

[模型陈列室](https://codezzzsleep.github.io/next-zenith-beforestep/gallery.html)可旋转真实 GLB、查看任务与核对信息；[图文来源与 SHA-256](docs/readme/m20-bright-20261119/sources.json)保留原照片和亮版 M20 展示资产的身份。

---

## 二、核心基准结果

运动与接触结果来自 **MuJoCo 物理仿真**。生成调用与几何诊断另有台账：累计口径见 [production-v6/facts.json](evidence/production-v6/facts.json)，较早归档节点见 [route/lux-usage.json](evidence/crossing/route/lux-usage.json)。

| 测试维度 | 对照基线 | BeforeStep 实测 |
| :--- | :--- | :--- |
| **R1 窄道导航** | 乐观（仅可见面）：**80.87 s 碰撞**<br>保守（未知全堵）：**142.20 s 停车** | **112.84 s 无碰撞到达**（1 次观察 · 12 世界完整预演通过 · 最小 3D 净空 **47.541 mm**） |
| **场景变体评估（17 场）** | 12 已知 + 5 留出场景；原想象 **4 次碰撞** | 最终赛后修订 **3 到达 / 14 停车 / 0 碰撞**（已知 3 通 9 停 · 留出 5 停） |
| **观测核对与背面偏差** | 被拒候选反事实干预：**17/102 碰撞** | 通过核对的 64 份候选中，仍有 **23/64** 背面偏短超过 5 cm；正面吻合不保证未知背面正确 |
| **低门槛通行（10/12/15 cm）** | 轮行：**0/90** 通过 | 逐腿跨越：**24/24** 干净通过；真实石体几何 **3/3**，可见矮坎直接交给轮腿执行 |
| **Lux3D 真实任务账本** | — | 累计 **491 创建 / 460 成功 GLB / 31 失败**；V5 Beta 归档节点 **467 / 438 / 29** |

表中秒数使用原实验的**仿真时钟**。17 场中的 12 场是赛后修订复测，5 场为指定留出；零碰撞伴随较多停车。观测核对与完整预演通过后仍可能发生独立执行碰撞，恢复黑影深度的对照也能到达。轮腿校准仅覆盖 10、12、15 cm 的冻结 Go2W 仿真条件，未连续验证其间高度或 M20 实机。反事实干预次数与几何诊断份数分别计数。

[R1 原结果](docs/reviews/RESULT_BEFORESTEP_R1.md) · [R2 核对与反事实](docs/reviews/RESULT_BEFORESTEP_R2.md) · [R3 方法比较](docs/reviews/R3-method-tables.md) · [轮腿校准与边界](docs/reviews/RESULT_WHEELLEG_CROSSING_FINAL.md) · [逐项事实与来源](docs/narrative-evidence-20261119.md)

---

## 三、快速开始与在线交互

### 本地零密钥复现

冻结研究链路需要 **Python 3.12、Git LFS 与可用的 MuJoCo OpenGL 环境**。按需拉取运行资源，复用已归档的真实 Lux3D 资产，无需 API 密钥、不产生新的云端生成费用：

```bash
# 1. 克隆仓库，按需获取运行资源
GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 https://github.com/codezzzsleep/next-zenith-beforestep.git
cd next-zenith-beforestep
git lfs install --local
git lfs pull --include="site/**,assets/runtime-*.tar.gz,assets/candidates/595*/tex_mesh.glb,evidence/reviews/beforestep_r1/lux/original_b/**,evidence/web-assets/**" --exclude=""

# 2. 初始化依赖环境（安装到 .venv）
./setup.sh

# 3. 完整复现冻结 R1，再启动本地作品站
MUJOCO_GL=egl .venv/bin/python ops/quickstart.py --reuse-lux --serve
```

该命令完成观测、候选核对、十二世界完整预演与独立执行，结果写入 `outputs/quickstart/`，随后在 <http://127.0.0.1:8080/> 提供作品站。[逐步复现与源码导览](docs/code-tour.md)说明输入、依赖与输出位置。

仅启动网页试玩时，克隆并拉取 `site/**` 资源后可直接运行 `python3 -m http.server 8000 --bind 127.0.0.1`，打开 <http://127.0.0.1:8000/site/play.html>。

### 在线四站试玩按键

[打开云深处山猫 M20 驾驶舱](https://codezzzsleep.github.io/next-zenith-beforestep/play.html)，按 **Enter** 开始，体验 **1 观测 → 2 局部想象 → 3 预测 → 4 探索**。

<a href="https://codezzzsleep.github.io/next-zenith-beforestep/play.html">
  <img src="docs/readme/m20-bright-20261119/m20-exploration.jpg" width="100%" alt="V5 Beta 封面原图中的 M20 月面探索，轮腿结构清晰可辨">
</a>

| 按键 | 功能说明 |
| :--- | :--- |
| `Enter` | 开始月面任务 |
| `W / A / S / D` 或方向键 | 驾驶移动与转向 |
| `空格` | 刹车停稳 |
| `E` / `Q` | 现场补看 / 打开局部空间想象与候选对比面板 |
| `V` | 切换第一视角 / 第三视角 / 俯视 |
| `1–4` + `J / K / L` | 选中腿，再执行抬起 / 前移 / 落地；四腿共 12 个主要跨越动作 |
| `R` | 探索练习回到本局实际停稳检查点 |

**手控独立开放**。辅助路线必须通过所选全部世界的完整预演，许可绑定候选、路线、停稳姿态与本局观测版本；有效补看或改变选择会撤销旧许可。当前试玩复用已有原照片与真实候选，初始 **1 世界**、同图对比 **2 世界**；原 R1 的 12 世界另作为研究证据保留。

网页使用 [Deep Robotics LYNX M20](https://github.com/DeepRoboticsLab/deep_robotics_model/tree/main/M20) 公开外观模型，运动与碰撞保留原 Go2W 的 16 个执行器和控制器。桌面与 390 px 触屏模拟已完成整局，手机真机性能尚未测量。[操作与实现](docs/mission.md) · [练习、挑战与成绩](docs/playability.md) · [真实试玩验收](docs/judges-demo.md)

---

## 四、仓库目录结构

```text
next-zenith-beforestep/
├── src/beforestep/           # 冻结研究链路：观测、生成、配准、核对、规划与执行
├── site/                    # 展示站与在线任务：index、play、gallery、levels、report
├── ops/                     # 启动与复现脚本：quickstart.py
├── assets/                  # 原输入、真实候选网格、运行资源与资产身份
├── docs/                    # 技术文档、迭代决策与公开依据
│   └── assets/              # 系统架构 SVG：forebrain-pipeline.svg 等
├── evidence/                # 实验日志、录像、结果与真实任务台账
│   └── crossing/route/      # lux-usage.json：任务 ID、状态与输入身份
├── reports/                 # V5 Beta 主报告与 V3、V4、V5 历史原件
└── setup.sh                 # 本地依赖与渲染环境初始化
```

[代码导览](docs/code-tour.md) · [项目目标](docs/project.md) · [工程决策](docs/decisions.md) · [资产总索引](assets/manifest.json)

---

## 五、归档资料与公开参考

<details>
<summary><b>点击展开：技术版本演进（V6–v0.3）与报告、视频素材索引</b></summary>

**技术迭代归档**：`V6`（观测约束融合）→ `V7`（双视角核对）→ `V8`（窄道候选）→ `v0.1`（模块化预演）→ `v0.2`（完整通行）→ `v0.3`（训练控制器）。各阶段保留源码、配置、输入、原模型、失败与结果。

<picture>
  <source media="(max-width: 600px)" srcset="docs/readme/m20-showcase/versions-mobile.png">
  <img src="docs/readme/m20-showcase/versions-desktop.png" width="100%" alt="六个核心技术版本的真实模型与输入：V6、V7、V8、v0.1、v0.2、v0.3">
</picture>

[交互资产对比](https://codezzzsleep.github.io/next-zenith-beforestep/award-assets.html) · [技术里程碑](docs/milestones.md) · [核心版本清单](evidence/award/asset-iterations/manifest.json)

**主报告 V5 Beta · 11 页**：[逐页阅读](https://codezzzsleep.github.io/next-zenith-beforestep/report.html) · [原 PDF](reports/v5-beta/report.pdf) · [版本与历史原文件](reports/README.md)。报告编号与技术版本分别记录。

**演示视频与原片**：[B 站主宣传片（BV1YZst6eEZk）](https://www.bilibili.com/video/BV1YZst6eEZk/) · [1080p 连续原片与补拍下载](https://github.com/codezzzsleep/next-zenith-beforestep/releases/tag/judges-demo-20261118) · [母片、五图与来源索引](evidence/judges-demo/README.md)。仓库保留用于 112 秒导演成片的原素材，[剪辑指南](docs/demo-edit-guide.md)列出镜头顺序和时间码。

</details>

- **3D 世界先验与接口**：[Manycore Tech PR Newswire（2026-08-27）](https://www.prnewswire.com/news-releases/manycore-tech-unveils-lux3d-and-an-explicit-3d-path-to-world-models-302861778.html) · [Aholo Lux3D OpenAPI](https://labs.aholo.ai/api-docs/specifications/services/lux3d/openapi.en.json) · [World Labs](https://worldlabs.ai/blog/marble-world-model)
- **视觉认知与部分观测研究**：[OpenStax Psychology 2e §5.3](https://openstax.org/books/psychology-2e/pages/5-3-vision) · [Saund & Berenson，CoRL 2020 / PMLR 2021](https://proceedings.mlr.press/v155/saund21a.html)
- **轮腿机器人模型**：[Deep Robotics LYNX M20](https://github.com/DeepRoboticsLab/deep_robotics_model/tree/main/M20)

[参考文献](docs/references.bib) · [来源与致谢](docs/credits.md) · [README 图文与重制方法](docs/readme/README.md)
