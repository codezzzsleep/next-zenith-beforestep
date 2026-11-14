# 先见一步 · BeforeStep

<!-- PHOTO-STORY-README-START -->
月面机器人只看得到石头朝向它的一面。Lux3D 替它把背面想出来；我们把生成结果当作假设，先核对观测，再在每一份准入想象里预演完整路线，全部安全才迈步。想象有用，也会出错；矮门槛的跨越靠看见的几何与轮腿动作。

[最新 Lux3D 核心 Demo · 2 分 37 秒](evidence/lux3d-demo/README.md) · [3 分 05 秒故事版与全部 39 条素材](evidence/production-v6/README.md) · [制作代码](tools/production_v6/README.md) · [原方法与失败](docs/reviews/STORY_V3.md)

[高石头绕行 R1 到 R3](docs/reviews/RESULT_BEFORESTEP_R1.md) · [同路两种石头的实际结果](docs/crossing.md)
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

## 轮腿与想象

首场四种车全部终态。原门槛石开发已收尾，四项物理闸门通过；同路两种石头的四车结果按原件公开，结论以 [结果表](docs/crossing.md#一条路上两种石头) 为准。

[交互页面](https://codezzzsleep.github.io/next-zenith-beforestep/crossing.html) · [实验规范](docs/reviews/SPEC_WHEELLEG_CROSSING_ADDENDUM2.md) · [故事](docs/story.md)。

## 源码、资产与版本证据

[代码导览](docs/code-tour.md)、[版本里程碑](docs/milestones.md)和[核心资产迭代](evidence/award/asset-iterations/manifest.json)保留各版本的源码、输入、原生成资产及失败对比；[原 README 与历史复现命令](docs/history/README-before-addendum2.md)原字节留档。

## 附录

学习模型保留历史记录；Arena 停在 2747/4000，未完成，原数据与失败证据保留。
