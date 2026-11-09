# 代码与资产来源

- **Aholo Lux3D**：核心候选 3D 资产由真实调用生成，任务与输入来源保存在资产清单、各目标结果和新增实验中。生成输入是项目仿真渲染的真实观察；不是拼接图冒充两图调用。
- **Poly Haven 扫描岩石**：`rock_07`、`rock_09`、`moon_rock_03`、`moon_rock_04`、`moon_rock_06`、`moon_rock_07`，CC0-1.0。每块原始作者、来源 URL、原始模型摘要位于运行资源中的 `rock.json`；许可证 <https://polyhaven.com/license>。等比缩放/朝向处理用于场景，视觉去饱和与双面渲染不改变物理碰撞几何。
- **Unitree Go2W 模型**：`unitreerobotics/unitree_mujoco`，固定提交 `1eb6642e3f3fdfb7fb13a9794fd6a2dd93ea0e7d`，BSD 3-Clause；原许可证随运行资源归档保留并解包至 `vendor/unitree_mujoco/LICENSE`。
- **MuJoCo、NumPy、SciPy、Trimesh、CoACD、Manifold3D、Pillow、Matplotlib 等**：Python 依赖与版本见 `requirements.txt`，遵循各上游许可证。
- **Google model-viewer 4.0.0**：作品页原始 GLB 查看器，固定本地发行文件；许可证见 `site/vendor/MODEL_VIEWER_LICENSE`。
- **程序化月壤、星空、地球与远山**：由项目代码生成，地球是风格化图像；不标为真实卫星影像。
- **文泉驿字体**：仅在安装了字体的机器上生成带中文的展示截图/视频；未将字体文件打包分发。

报告和页面中的几何对比来自实际保留的网格；运行画面来自真实 MuJoCo 轨迹。历史证据来源身份逐项记录，不把诊断替身作为模型生成结果。
