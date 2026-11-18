# 评审原片与剪辑素材

从[公开试玩](https://codezzzsleep.github.io/next-zenith-beforestep/play.html?v=601d86b5)进入。
[下载完整原片包](https://github.com/codezzzsleep/next-zenith-beforestep/releases/download/judges-demo-20261118/BeforeStep-judges-raw-20261118.zip)，
或[直接下载连续母片](https://github.com/codezzzsleep/next-zenith-beforestep/releases/download/judges-demo-20261118/00-full-run.mp4)。
完整包 193,588,699 字节，SHA-256 `ae91c2ef3a0b2543336653d197e1339019483288eb46ecb09f4efc7844008f59`。

原片为真实 RTX 4090 页面操作、原生 1920×1080、H.264 / yuv420p / CFR 30 fps，保留按键与指针反馈，配独立静音 AAC 轨。
母片全长 4:59.667，实际采集总体 28.06 帧/秒；行驶和十二次轮腿操作各约 29.72 帧/秒，静止画面无需重复采集。
编码采用 CPU libx264 CRF17；本实例实际 NVENC 探测失败。所有 MP4 全解码通过，具体时序见 capture JSON。

## 剪辑入口

| 文件 | 内容 | 来源与时间码 |
| --- | --- | --- |
| 00-full-run.mp4 | 普通入口、初判、想象、两世界预演、驾驶、12动作、信标结算 | 连续当前试玩，d6397c52，4:59.667 |
| 01-first-look.mp4 | 完整M20接近与受限第一眼、初判 | 母片 00:07.481–00:26.152 |
| 02-one-photo-two-backs.mp4 | 同一原图、两份真实背面、原可见面拒绝核对 | 对比原片 00:16.792–00:48.135，601d86b5 |
| 03-gap-and-route.mp4 | 固定同尺度地图、候选占地与真实两路线 | 对比原片 00:47.135–01:05.953 |
| 04a-release.mp4 | 两个世界真实完成，辅助出发获得许可 | 母片 01:04.983–01:27.216 |
| 04b-hold.mp4 | 换组撤销旧许可、真实补看、重复观测与主动停车 | 独立当前试玩，d6397c52；重点 00:40.403–01:01.300 |
| 05-drive-reveal.mp4 | 第一视角入缝与随后跟拍 | 母片 01:26.216–02:24.221；完整绕过高石至门槛见母片 01:27.216–03:02.227 |
| 06-legs-and-goal.mp4 | 低侧前机位、十二次抬/迈/落、轮行与信标 | 母片 03:01.227–04:56.250 |
| 02-03-space-comparison.mp4 | 清楚的模型与局部地图独立补拍 | 601d86b5，1:06.367；与母片分别标代码版本 |
| research/ | 原R1三策略、4×3十二世界、R3证据不足停车 | [研究索引](study-index.json)，原Go2W与原实验条件 |

所有秒数均为视频时钟；仿真秒单独保存在[章节](chapters/)。原速等待保留，导演可按精确入出点剪辑。
同图候选为5958948与5959025，另一高石固定5958934；5958642是真实被拒例子，只能查看。
灰线、金线和余量读取真实规划，5cm投影栅格余量不等于接触测量，也不保证灰线必碰。
本局两世界与原R1十二世界分别计数。

当前04b是过期许可被撤销后玩家选择停车。原R3 F2_011两批第二眼12任务、10成功返回、零准入而停车，
是[单独列明来源的研究回放](study-index.json)，不把它描述为这局自动触发。
M20是试玩外观，MuJoCo控制和原研究保留Go2W条件；原照片进入Lux3D，已有RGB-D用于本地核对/配准。
当前试玩复用真实已生成资产，不提交新的生成请求。导演负责约112秒成片、中文配音、音乐、字幕与转场。

## 五张原尺寸图

完整包中的PNG均1920×1080，直接从真实原片取帧。仓库保留同一帧的JPEG供浏览：

1. [受限第一眼](figures/01-limited-first-look.jpg)：母片00:21.975。
2. [同图两候选与核对](figures/02-one-photo-two-backs-and-checks.jpg)：对比原片00:32.496。
3. [占地与真实路线](figures/03-footprint-and-route.jpg)：对比原片01:02.971。
4. [预演决策](figures/04-rehearsal-decision.jpg)：母片01:26.846。
5. [M20轮腿行动](figures/05-M20-leg-action.jpg)：母片03:36.368。

[完整素材清单](manifest.json)逐项记录下载、SHA-256、尺寸、帧率、代码版本、任务、事件和结果；
[公开入口桌面验收](verification/public-desktop-v2.json)与[触屏模拟验收](verification/public-touch-v2.json)
各完成6阶段、2世界、12动作与到达，零页面错误、无姿态注入、无本地资产镜像。手机真机性能未测。
后续比较布局经两端实际按钮与地图可见性检查，最终原片验证地图完整可见、候选标签仅26px高，原模型材质未改。
公开下载的匿名SHA与解码验证以 verification/public-downloads.json 为准。

## 复现录制

```sh
python tools/beforestep_mission/record_judges_demo.py --root /path/to/runtime --url http://127.0.0.1:8000/site/play.html --out /path/to/new-output --chromium /path/to/chromium
python tools/beforestep_mission/record_judges_hold.py --root /path/to/runtime --url http://127.0.0.1:8000/site/play.html --out /path/to/new-hold --chromium /path/to/chromium
python tools/beforestep_mission/record_judges_comparison.py --root /path/to/runtime --url http://127.0.0.1:8000/site/play.html --out /path/to/new-comparison --chromium /path/to/chromium
```

依赖Playwright、ffmpeg和可用NVIDIA EGL浏览器。录制使用SHA一致的原资源镜像；公开验收省略`--asset-root`，不把镜像录制当成公网加载性能。
