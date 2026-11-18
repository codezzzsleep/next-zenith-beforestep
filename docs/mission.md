# BeforeStep 月面探索任务

[打开月面探索](https://codezzzsleep.github.io/next-zenith-beforestep/play.html)。目标是绕过高石、跨过可见矮坎，在青色信标里停稳。当前玩法以[评审试玩](judges-demo.md)及其 2026-11-18 实际验收为准；项目主报告为 V5，主宣传片为作者已发布的[B站视频](https://b23.tv/4CAPaLu)。

## 从初判到行动

点开始或按 Enter 后，WASD / 方向键驾驶、空格刹车。机器人在高石观察点通过电机制动停稳，切到当前第一视角，先看三秒再记录“能过、绕开或拿不准”。石体、原扫描贴图、月壤和低角度太阳始终完整，遮挡由实际场景形成。

初判后有四种自主选择：自己开、让 Lux3D 想一想、再看一眼或停车。手控独立开放；预演许可约束辅助路线。按 Q 打开空间想象，E 用当前相机的真实传感射线补看，V 切第一、第三或俯视。手机使用摇杆与对应按钮。

空间想象展示同一张原 R1 RGB 输入与两份真实 A 候选，再把候选配准到局部通道中，比较占地与路线。启动默认 A:C1（5958948）与固定 B:C1（5958934）形成一个世界；点击“同时考虑两份假设”加入 A:C2（5959025）后形成两个世界，这是评审原片和公开整局验收的选择。另保留 B:A1（5958642）的拒绝例。玩家也可以选择已有的其他准入候选，组合数量按实际选集计算。原 R1 六份 A × 两份 B 的十二世界研究单独保留。

Lux3D 只提供物体级静态几何假设；RGB-D、位姿和已知地形用于本地配准与核对，MuJoCo 计算机器人运动和碰撞。网页复用已有真实输入与模型，没有把当前相机帧提交给云端生成。“前额叶”是这一空间想象模块的角色比喻。

## 真实预演、辅助许可与手控

停稳后选一条路线进行预演。所选原配准 GLB 网格构成独立 MuJoCo 碰撞世界，同一机器人靠原执行器实际走完候选路线。只加载或旋转模型不等于试路通过，未完成和取消的结果不提供许可。

辅助许可同时绑定候选修订、路线、当前停稳位置、朝向和本局观测版本。改变选择、增加有效观测或改变起点使旧许可失效；旧记录继续保留为对应快照的试路记录。执行途中方向键或摇杆可以接管。恢复辅助只续走原已验证路径，离开路线后要重新试路。

新增观测只包含当前射线确实命中的表面，不把隐藏场景网格填入认知地图。完整外部场景用于显示与独立物理执行；可见占地、背面假设与执行后揭晓分别标注。候选核对和预演通过仍不保证真实未知背面正确，灰色参考路线的结果按实际预演显示。

## 轮腿跨越与抵达

高石之后的可见门槛可以先尝试轮行、直接迈腿，或用已测几何进行跨越预演。门槛约高 12 cm、宽 10 cm，轮半径约 8.6 cm。按 1–4 选腿，J 抬起、K 前移、L 落地，亲手触发四腿的 12 个主要动作。控制器辅助重心、平衡及支撑准备。

进入约 35 cm 目标圈且四轮越过门槛后，电机制动并判定抵达。探索练习可按 R 恢复最近的实际停稳检查点；全程挑战从起点一次完成。恢复明确属于重置，会取消旧任务、清空预演许可，并恢复检查点当时的观测和记录。[模式与成绩规则](playability.md)。

M20 是当前试玩的显示外观，动力学、碰撞与 16 个执行器继续复用冻结 Go2W 条件。原 R1 研究画面保留原机身标识，新的游玩成绩和录像与 R1/R2/R3 分开计数。

## 代码与来源

| 模块 | 职责 |
| --- | --- |
| `mission-worker.js` / `mission-world.js` | 持续真实物理世界、独立预演、射线观测和事件 |
| `mission-observation.js` / `mission-session.js` | 本局知识图层、许可身份与失效规则 |
| `mission-showcase.js` / `mission-story.js` | 初判、四种选择与操作引导 |
| `mission-planner.js` / `mission-insight.js` | 候选占地、路线、可解释的真实结果 |
| `mission-scene.js` / `mission-appearance.js` | 同一快照的视角、完整原材质与 M20 外观 |
| `mission-run.js` / `mission-gameplay.js` | 练习、挑战、成绩与复盘 |

除明确重置与独立预演初始化外，机器人位姿来自执行器力矩和 MuJoCo 求解。第一、第三、俯视及画中画消费同一真实状态，脑内世界单独标注。源码、模型与输入见[代码导览](code-tour.md)、[资产清单](../site/media/mission/manifest.json)和[当前原片索引](../evidence/judges-demo/README.md)。

## 本地运行与验证

按 [README](../README.md#本地运行)拉取站点 LFS 资产，再在仓库根运行 `python3 -m http.server 8000 --bind 127.0.0.1`，打开 `http://127.0.0.1:8000/site/play.html`。默认复用已有生成，不需要 API 密钥。

```sh
node tools/beforestep_mission/check_judges.mjs /tmp/beforestep-judges.json
node tools/beforestep_mission/check_worker_mission.mjs /tmp/beforestep-worker.json --showcase
python3 tools/beforestep_mission/check_judges_browser.py --help
```

当前桌面与 390×844 触屏模拟已各通过六阶段、两世界、12 动作和实际抵达；[公开验收](../evidence/judges-demo/verification/)保留原结果。此前阶段的检查见[体验验证历史](game-experience-verification.md)。部署继续保留 [Pages 固定素材映射](pages-delivery.md)。
