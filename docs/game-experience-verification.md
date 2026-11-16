# 月面探索体验的实际验证

2026-11-16 的新游戏沿用 v3 报告视觉，验证对象是新增的交互体验。原 R1 / R2 / R3 输入、生成记录、阈值、六版对照和实验结果保持独立。

| 检查 | 实际结果 |
| --- | --- |
| 原完整任务物理检查 | 12 个真实候选碰撞世界全部完成；真实月面同路线通过；门槛跨越和终点通过 |
| 原任务对照 | 只按可见面的走法发生高石接触；纯轮行未让四轮通过门槛 |
| 新体验与认证 | 选择修订、未完成/取消、起点位置、朝向、速度、车身姿态限制有效；不同选集改变组合数量，走法改变路线 |
| 独立真实与脑内世界 | 预演推进没有替换或修改真实机器人的位姿；当前控制姿态目标复制到预演初始化 |
| 可见与未知 | 真实射线命中高石表面；转向后可见表面改变；第一、第三、俯视均使用已观察的表面 |
| 完整 worker 任务 | 默认两模型组合预演、真实绕行、当前门槛试跨、12 个玩家命令、恢复轮行、抵达；完成事件和终态快照一致 |
| 桌面实际浏览器 | 先键盘驾驶，再观察/切视角、载入并转动原 GLB、选择/取消预演、接管与恢复路线、12 次抬迈落、实际到达完成画面 |
| 三相机及画中画 | 1280 和 390 宽度下，暂停后逐个切换第一/第三/俯视，实际快照与画中画时间完全相同 |
| 手机交互 | Chromium 真触屏事件模拟：摇杆与刹车、三视角、原模型及固定操作按钮、取消、选腿抬起、落地回轮行，六项通过 |
| 显示 | 桌面和手机无横向溢出；原 GLB 实际加载并拖动旋转；中文字体覆盖当前界面全部汉字 |
| 原资料保留 | 原碰撞资源、规划与轮腿控制器字节未改；原 PDF SHA-256 仍为 67c15f4af8c02c79c4254e55774207acf51796784583e58543c5d482c0199cc6 |

录像为实际浏览器键盘与鼠标验收，画面来自运行中的 WebGL / MuJoCo。物理状态没有由验收脚本注入。四腿的 12 个主要动作由按键触发；必要的重心与支撑准备由原控制器辅助。

录制时已经收到实际抵达事件、显示探索完成卡。帧率限制曾漏发最后的状态快照，使自动检查读到旧的轮行阶段；已强制推送抵达和失败终态，并通过完整 worker 任务回归。录像保留真实连续流程，结束于完成画面，不用预录片段充当脑内预演。

当前验证使用软件 WebGL，手机部分为触屏模拟，未做真实手机的性能基准。模型符合原观测及所选世界的预演通过仍不保证未知背面正确。数据和画面见 [本次证据](../evidence/game-experience-20261116/README.md)。

复现（Node 22+，Python Playwright 与 Chromium）：

```sh
node tools/beforestep_mission/check_mission.mjs /tmp/original-mission-physics.json
node tools/beforestep_mission/check_experience.mjs /tmp/game-experience.json
node tools/beforestep_mission/check_worker_session.mjs /tmp/game-session.json
node tools/beforestep_mission/check_worker_mission.mjs /tmp/game-complete.json
python3 tools/beforestep_mission/check_browser.py \
  --url https://codezzzsleep.github.io/next-zenith-beforestep \
  --output /tmp/beforestep-browser/result.json
```
