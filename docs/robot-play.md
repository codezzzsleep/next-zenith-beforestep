# 亲手操作轮腿机器人

本文保留早期三关驾驶练习，入口为[历史驾驶舱](https://codezzzsleep.github.io/next-zenith-beforestep/play-practice.html)。当前 M20 显示外观、初判/想象/补看/停车的月面任务见[最新操作说明](mission.md)，主报告为 [V5 Beta](../reports/README.md)。早期练习让观众实际驾驶和逐腿操作原 Go2W 机器人。三个任务分别练习轮行与抬腿、跨过门槛、查看完整模型后绕行。

## 怎么操作

WASD / 方向键驾驶，空格刹车。1 / 2 / 3 / 4 选择右前、左前、右后、左后腿；J 抬起、K 前移、L 落地。手机点击同样的选腿和动作按钮，摇杆用于轮行。画面中的圆环标记当前腿，面板显示实际接地载荷。

第一项任务先到绿色区域停稳，再亲手完成一条腿的抬、移、落。第二项任务是横贯通道的 12cm 门槛；点击“进入逐腿跨越”，系统调整重心与支撑，四条主要跨越腿的抬起、前移、落地分别等待玩家触发，共 12 个动作。全部落地后回到轮行，开到终点停稳。第三项任务的高石超出这组抬腿动作的能力，完整生成模型帮助玩家选择绕行。

## 实时动作怎样执行

官方 `@mujoco/mujoco` 3.17.0 单线程 WASM 在独立 Web Worker 中推进 2ms 物理步骤，Three.js 0.170 显示当前状态。16 个轮腿执行器接收电机力矩；控制过程不写机器人位置或播放预存轨迹，重置才设置初始姿态。

新的 [wheelleg-control.js](../site/wheelleg-control.js)从项目冻结 v72 控制器独立移植解析逆运动学、接触力测量、重心调整和静力补偿。它提供通用单腿操作和带玩家动作闸门的跨越流程。跨越的支撑调整自动执行，四条主要跨越腿的动作由玩家逐步触发。原 v72 源码、正式标定与实验结果没有修改。

## 资产与模型怎样参与

机器人是本项目已有的 Unitree Go2W MJCF、网格、关节、惯性和执行器；月面重力是1.62m/s²，物理时间步长2ms。公开的 [资产清单](../site/media/robot-play/manifest.json)保留原文件身份、派生数据和原授权来源。

第三项任务复用已有真实任务5958685、5958654的生成几何及其原配准矩阵。绿色模型和参考路线来自这些生成几何，机器人相机的小窗口显示当前场景。移动机器人不会创建新的 Lux3D 请求。参考路线使用12cm格子和驾驶体验的余量，实际石头的物理接触可以否决路线，届时玩家接管。查看[原照片和生成模型](https://codezzzsleep.github.io/next-zenith-beforestep/gallery.html)可继续理解模型从哪里来。

显示网格做确定性的格子聚合，以减少浏览器绘制开销；原物理网格和生成模型原件完整保留。三关为独立驾驶场景，使用扫描石头的已有形状；场景与操控规则不等同于冻结实验。研究中的RGB-D观测核对、5cm规划与完整多世界预演、全部原成功和失败仍在[项目报告](report.md)和原记录中。

## 本地打开

页面包含已经打包的物理引擎与机器人资产，不要求 Python 仿真依赖或云服务密钥。克隆后从HTTP服务器打开：

```bash
python3 -m http.server 8000 --directory site
# 浏览器打开 http://localhost:8000/play-practice.html
```

需要支持 WebGL、WebAssembly、ES模块Web Worker和gzip DecompressionStream的现代浏览器；不支持时会提供视频入口。

具备本项目完整原资产的工作区，可以重新打包机器人和显示数据：

```bash
python3 tools/robot_play/build_assets.py --source . --output site/media/robot-play
```

打包使用项目现有的 NumPy、SciPy 和 trimesh 依赖。原资产缺失或只有LFS指针时，先按项目恢复说明取得原件。物理WASM、Three.js与Unitree模型分别保留官方来源和许可证；打包代码不会提交云生成任务。

## 独立功能验证

```bash
node tools/robot_play/check_controls.mjs site controls.json
```

此检查运行新游戏控制器：四条腿分别真实离地、前移和承重落地；三种车身高度、两种轮速在同一门槛前的轮行；跨越在 12 个闸门处等待输入、全部脚轮过线、恢复轮行，以及跨越时的非轮碰撞与倾角。它不运行冻结研究实验。实际检查结果见 [操作功能验证](robot-play-verification.json)。
