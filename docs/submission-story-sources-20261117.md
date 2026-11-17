# 完整参赛故事：事实与来源

本页对应[完整参赛故事稿](submission-story-20261117.md)。核对日期为 2026-11-17；外部资料用于确认术语与技术背景，作品效果只引用本项目已有实验记录。

故事主线是：普通图片 → 三维几何候选 → 观测核对 → 局部空间模型 → 路径规划与完整物理预演 → 行动、补看或停车。

## 表述与依据

| 需要说明的事实 | 依据与适用范围 |
| --- | --- |
| Lux3D 图生三维接口接收普通图片 | S1、S2。`ImgTo3dRequest` 要求 `img`、`imgs` 二选一，没有必需的深度图字段。项目[提交代码](../src/beforestep/generation/client.py)上传图片 URL；完整项目仍使用深度辅助提取、配准和核对。 |
| Lux3D 返回的几何参与局部环境建模 | [几何处理](../src/beforestep/geometry/imagination.py)将候选配准、核对并转换为世界坐标网格与占据；[导航地图](../src/beforestep/navigation/map.py)将生成占据用于路线计算。不是由接口直接返回完整环境地图。 |
| 系统在内部环境假设中判断行动后果 | [研究主链](../src/beforestep/pipeline.py)逐候选组合运行完整物理预演，然后在独立环境执行。Lux3D 提供静态几何，MuJoCo 提供运动和碰撞计算。 |
| 三维空间生成属于世界模型的一个方向 | S3 明确把三维重建、生成和仿真纳入世界模型。S1 将 Lux3D 定位为三维生成，并说明与 World API 互补；已查资料没有明确证明 Lux3D 自身是通用世界模型，故采用“基于 Lux3D 的局部世界建模”。 |
| 人可以从图像线索推断空间 | S4 介绍单眼深度线索，包括透视、遮挡和相对大小。颜色深浅本身不能唯一决定距离；机器人也可借助几何与学习算法获得空间表征，S5 提供机器人形状补全实例。 |
| LiDAR 与 SLAM 存在资源开销 | S6 将执行时间、内存和能耗纳入 SLAM 评测，S8 给出一款传感器的功率。S7 说明 SLAM 可以增量建图。本作品尚无相同任务下的整链能耗对照，节能只作研究动机。 |
| R1 中生成几何与预演支持一次观察后到达 | [R1 原始执行记录](reviews/RESULT_BEFORESTEP_R1.md)：12 个候选世界全部预演完成、无碰撞；独立执行一眼、112.84 仿真秒到达。乐观策略碰撞，保守策略停车；see-dark 对照也到达。 |
| 扩展实验暴露了隐藏形状判断的风险 | [R2 原始结果](reviews/RESULT_BEFORESTEP_R2.md)：决定性 8 场为 3 到达、3 停车、2 碰撞。[R3 比较表](reviews/R3-method-tables.md)：最终修订已知 12 场为 3 到达、9 停车、0 碰撞，指定留出 5 场全部停车、0 碰撞。 |
| 候选符合观测不等于隐藏部分正确 | [报告中的逐候选诊断](report.md)：原 R1/R2 的 64 份准入候选中，23 份沿观测前进轴的背面端点比关联真值短超过 5 cm；真值只用于赛后诊断。 |
| 轮腿跨越属于可见几何下的执行能力 | [轮腿原始说明](crossing.md)：已测试的 10、12、15 cm 三个离散高度中，常规和高姿态轮行 0/90 通过、逐轮跨越 24/24 干净通过。跨越结果不用于证明 Lux3D 对低门槛的必要性。 |
| M20 有官方公开模型资源 | S9 提供 MJCF、URDF 与分件网格。只做显示层适配无需重训原控制器，但关节、尺寸和连杆坐标需要映射；现有实验与游戏仍使用原 Go2W，M20 外观尚未替换。 |

## 外部原始来源

### S1 · Aholo 官方 API 介绍

https://labs.aholo.ai/api-docs/en/intro

Lux3D 一节描述为“3D generation with a focus on high-quality PBR materials, complementary to 3DGS world APIs”，并列出 Image to 3D 能力。该说明支持图生几何定位，不提供机器人动作动力学、训练数据规模或通用世界模型的技术证明。

### S2 · Lux3D 官方 OpenAPI

https://labs.aholo.ai/api-docs/specifications/services/lux3d/openapi.en.json

`POST /global/lux3d/v1/generate/img-to-3d/task/create` 的 `ImgTo3dRequest` 字段为 `img`、`imgs`、`version`、`faceCount`、`outputFormat`、`enablePbr`、`aiPredictSize`。规范说明 `img`、`imgs` 必须二选一；生成尺寸预测不代替本项目对现场尺度的观测核对。

### S3 · World Labs：Marble 世界模型

https://worldlabs.ai/blog/marble-world-model

原文提出“World models should reconstruct, generate, and simulate 3D worlds”，并介绍从图文等输入生成三维世界的 Marble。它说明世界模型语境包括空间生成方向；不能将 Marble 的能力直接归给 Lux3D 或本项目。

### S4 · OpenStax Psychology 2e：视觉与深度知觉

https://openstax.org/books/psychology-2e/pages/5-3-vision

第 5.3 节解释单眼、双眼深度线索及视觉空间表征。用于支持“图像可以提供空间线索”，不把人的推断能力写成无条件准确，也不把机器人描述为无法获得空间感知。

### S5 · CoRL / PMLR：不完整深度图的多种合理形状补全

https://proceedings.mlr.press/v155/saund21a.html

Saund、Berenson，*Diverse Plausible Shape Completions from Ambiguous Depth Images*。用于说明不完整观测可对应多个形状假设，以及机器人可以利用补全几何；不是本项目方法效果或实机能力的证据。

### S6 · SLAMBench：性能、精度与能耗评测

https://arxiv.org/abs/1410.2163

https://github.com/pamela-project/slambench

SLAMBench 将质量、执行时间、内存和能耗作为可测指标。用于说明资源成本需要实测，不据此声称我们的生成与预演流程已经比 SLAM 更省电。

### S7 · FAST-LIO：增量建图

https://github.com/hku-mars/FAST_LIO

官方仓库明确列出“Incremental mapping using ikd-Tree”。用于纠正“SLAM 必须先构建完整环境地图”的说法；SLAM 是定位与建图方法，LiDAR 是测距传感器。

### S8 · Livox MID-360 官方规格

https://www.livoxtech.com/mid-360/specs

规格列出平均功率 6.5 W，低温自加热时峰值可能达到 14 W。这是一款传感器的规格，不是整套 SLAM 系统的能耗，也不能与本项目未测的总能耗直接比较。

### S9 · 云深处 M20 官方产品与模型

https://www.deeprobotics.cn/products/detail/1.html

https://github.com/DeepRoboticsLab/deep_robotics_model/tree/main/M20

用于确认山猫 LYNX M20 轮足机器人及公开模型资源。公开资源可用不等于已完成外观适配或 M20 动力学验证。

## 本项目证据的读取原则

研究实验时间是仿真时钟，云端生成、配准与完整预演的墙钟另计。原研究运行、记录回放、当前网页实时仿真和新增游戏成绩分别说明；主报告仍为 V3，完整故事用于解释已有成果。原始输入、生成模型、准入门槛、失败记录与实验结果按原件保留。
