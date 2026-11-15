# BeforeStep 月面操作任务

打开 [月面任务](https://codezzzsleep.github.io/next-zenith-beforestep/play.html)：观察高石的正面照片，核对 Lux3D 的完整候选，在模型构成的世界中预演，再驾驶同一台轮腿机器人绕行、逐腿跨越门槛并抵达终点。

Lux3D 生成完整形状；BeforeStep 将生成模型配准到观测坐标，按可见轮廓、尺寸、表面贴合、未知部分与已知空地筛选，规划路线并运行多候选物理预演，最后让机器人执行。这里的模型作为真正的碰撞几何参与计算。改变候选集合会改变规划占据和 A × B 预演世界，路线须在所有所选组合中通过，才能执行。

任务复用原 R1 的记录观测、真实返回模型、配准后的世界网格和五项核对门槛。11 份候选中 8 份通过，与原记录一致；完整选择组成 12 个世界。浏览器重新执行规划、物理预演和运动控制，云端生成不在游玩时重新请求。候选原 GLB 可用官方 Aholo Viewer 旋转查看。

高石区域沿用 R1 的月面地形和碰撞场景。后面增加一段可见的 12 cm × 10 cm 门槛，让轮腿操作接在同一任务中。机器人相机射线测量门槛，测量结果进入跨越控制；深度加 4 mm 射线采样余量。四条腿的抬起、前移、落地由玩家分别触发，重心与支撑调整由控制器辅助。运动通过原 Go2W 的 16 个执行器力矩计算；重置以外不赋机器人位姿。

WASD / 方向键和手机摇杆控制轮行，空格刹车；1–4 选右前、左前、右后、左后腿，J 抬起、K 前移、L 落地。可以接管绕行、暂停、切换车载视角和俯视，跨越后恢复轮行，驶入与到达判定一致的 35 cm 绿色圆圈，控制器通过轮子制动停稳。旧三项自由练习保留在 [练习页](https://codezzzsleep.github.io/next-zenith-beforestep/play-practice.html)。

原 5 cm 规划图、0.40 m 直行净空和 0.57 m 转向净空保持不变；这个交互控制器额外留 7 cm 跟随余量，逐段停稳转向、沿线纠偏。原科学控制器、冻结规则、输入和结果都保留，本页任务分数独立于 R1 / R2 / R3。

## 验证与复现

独立物理验证覆盖五项准入一致性、12 个真实候选碰撞世界、真实场景执行、相机门槛测量、12 个跨越动作、四轮完全过线与恢复轮行到达。相同场景的可见表面路线发生高石接触，纯轮行未能跨越门槛。结果见 [验证记录](mission-verification.json)。这些结论对应本任务及此候选集合，不扩展为任意生成模型的安全保证。

用 Node 运行完整功能验证：

```sh
node tools/beforestep_mission/check_mission.mjs /tmp/mission-verification.json
```

资产构建：

```sh
PYTHONPATH=src python tools/beforestep_mission/build_assets.py \
  --source . --output site/media/mission --cache /tmp/beforestep-mission-assets
```

构建依赖项目已有的 Python / NumPy / trimesh 环境，只读取原证据并在指定缓存写派生资源。物理网格不简化；显示网格的确定性聚合用于浏览器绘制，原 GLB 和冻结资产保持原件。来源与摘要在 [资产清单](../site/media/mission/manifest.json)。
