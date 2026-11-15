# 亲自驾驶轮腿机器人

[在线驾驶舱](https://codezzzsleep.github.io/next-zenith-beforestep/play.html)让观众通过键盘或手机触屏驾驶机器人。第一关练习前进、转向和腿姿态；第二关用既有 Lux3D 模型观察几何与参考路线；第三关试驾低台阶，也可以选择绕开。

| 操作 | 控件 |
| --- | --- |
| 前进 / 后退 / 转向 | WASD、方向键、左下触屏摇杆 |
| 刹车 | 按住空格或右下刹车 |
| 升高 / 标准 / 蹲伏 | 轮腿姿态按钮 |
| 跟随 / 机器人视角 / 俯视 | V 或切换视角 |
| 已有模型与参考路线 | 第二关按 H 或模型辅助按钮 |
| 按参考路线驾驶并接管 | 模型驾驶按钮；方向键或摇杆随时接管 |
| 重新开始 | R 或重新开始按钮 |

机器人动力学在专用 Web Worker 中用官方 `@mujoco/mujoco` **3.17.0** 的单线程 WASM 运行，渲染使用 Three.js 0.170。实际动作写入16个轮腿执行器的控制量，前进、转向、关节姿态、接触与倾覆都由物理引擎计算。失焦、隐藏页面和松开触屏会清除驾驶指令。重置才设置初始位置；到终点会以电机刹车停稳。

## 资产与模型怎样参与

机器人是本项目已有的 Unitree Go2W MJCF、网格、关节、惯性和执行器；月面重力是1.62m/s²，物理时间步长2ms。公开的 [资产清单](../site/media/robot-play/manifest.json)保留原文件身份、派生数据和原授权来源。

第二关复用已有真实任务5958685、5958654的生成几何及其原配准矩阵。绿色模型和参考路线来自这些生成几何，机器人相机的小窗口显示当前场景。移动机器人不会创建新的 Lux3D 请求。参考路线使用12cm格子和驾驶体验的余量，实际石头的物理接触可以否决路线，届时玩家接管。查看[原照片和生成模型](https://codezzzsleep.github.io/next-zenith-beforestep/gallery.html)可继续理解模型从哪里来。

显示网格做确定性的格子聚合，以减少浏览器绘制开销；原物理网格和生成模型原件完整保留。三关为独立驾驶场景，使用扫描石头的已有形状；场景与操控规则不等同于冻结实验。研究中的RGB-D观测核对、5cm规划与完整多世界预演、全部原成功和失败仍在[项目报告](report.md)和原记录中。

## 本地打开

页面包含已经打包的物理引擎与机器人资产，不要求 Python 仿真依赖或云服务密钥。克隆后从HTTP服务器打开：

```bash
python3 -m http.server 8000 --directory site
# 浏览器打开 http://localhost:8000/play.html
```

需要支持 WebGL、WebAssembly、ES模块Web Worker和gzip DecompressionStream的现代浏览器；不支持时会提供视频入口。

具备本项目完整原资产的工作区，可以重新打包机器人和显示数据：

```bash
python3 tools/robot_play/build_assets.py --source . --output site/media/robot-play
```

打包使用项目现有的 NumPy、SciPy 和 trimesh 依赖。原资产缺失或只有LFS指针时，先按项目恢复说明取得原件。物理WASM、Three.js与Unitree模型分别保留官方来源和许可证；打包代码不会提交云生成任务。
