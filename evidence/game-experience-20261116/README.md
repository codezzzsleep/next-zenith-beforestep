# BeforeStep 新版月面探索实际运行

游戏入口：https://codezzzsleep.github.io/next-zenith-beforestep/play.html?v=immersive-1

`BeforeStep-immersive-mission.mp4` 为连续的实际浏览器键盘/鼠标验收录屏：驾驶、第一/第三/俯视、Lux3D 原模型、两个真实碰撞模型世界预演、辅助路线与接管、相机门槛预演、四腿 12 次主要动作、回轮行并实际抵达。

影片为 469 秒（7 分 49 秒）、1280 × 800、25 fps 容器帧率、H.264，默认关闭音效。只截去抵达画面后的静止尾段。没有物理状态注入、预制通关动画或用录像冒充在线预演。截图来自实际游戏和录像；原始高分辨率帧在本机保留。

| 文件 | 画面 |
| --- | --- |
| desktop-first.jpg | 相机看见高石正面，后面仍未知 |
| desktop-third.jpg | 同一时刻的机器人与周围已观察部分 |
| desktop-thought.jpg | 原始 Lux3D GLB 出现在机器人思想气泡中，可旋转 |
| mobile-thought.jpg | 手机上方机器人/相机，下方脑内模型，摇杆与刹车保持可用 |
| mobile-controls.jpg | 手机实际触屏操作后回到轮行 |
| robot-legs.jpg | 实际轮腿动作与选中腿反馈 |
| arrived.jpg | 实际探索完成卡，12 次动作、2 个模型世界 |

游戏复用项目真实返回与原始输入；未提交新 Lux3D 生成。官方 Aholo Viewer 显示原 GLB，所选配准网格参与 MuJoCo 碰撞。生成假设和实际环境分别标注，本次结果独立于 R1 / R2 / R3。

验收发现并修复了节流时漏发终态快照的问题：录像中的抵达事件与完成卡已经真实发生，修复后的全任务 worker 检查确认最后快照为 complete。新版另细化了手机思考布局、姿态认证与轮腿接管。运行数据在 verification.json，文件身份在 manifest.json；验证范围与复现见 ../../docs/game-experience-verification.md。
