# 空间前额叶与轮腿：叙事和证据

核对日期：2026-11-19。本页为 README 与首页补充来源和统计身份；报告 V5、原 R1/R2/R3 研究及其历史结果保持原件。

## Lux3D 的三维先验怎样进入局部世界模型

[群核科技发布稿，2026-08-27](https://www.prnewswire.com/news-releases/manycore-tech-unveils-lux3d-and-an-explicit-3d-path-to-world-models-302861778.html)原文说明：

> Lux3D was trained on a combination of generated and reconstructed physical-world data to improve geometric and visual consistency.

这支持把 Lux3D 视为具有三维几何与视觉先验的生成模型，也提供了其与显式三维世界模型路线的关系。稿件说明详细基准另行发布；本项目未独立核验训练集、训练方法或物理推理性能。训练素材含物理世界重建数据，不等于模型已经学习了机器人动作动力学。

[官方 OpenAPI](https://labs.aholo.ai/api-docs/specifications/services/lux3d/openapi.en.json)确认图生三维接口接收 `img` 或 `imgs` 普通图片。API 规范用于核验输入与接口能力，训练数据的依据是上述发布稿。

BeforeStep 将真实返回的物体网格配准到通道，用观测约束筛选、计算占地与路线，并交给 MuJoCo 逐世界预演。**Lux3D 提供几何假设，BeforeStep 构建局部世界，MuJoCo 计算行动后果。**“空间前额叶”是先想后走的模块比喻。

[World Labs：Marble](https://worldlabs.ai/blog/marble-world-model)提出“World models should reconstruct, generate, and simulate 3D worlds”，支持三维空间生成的世界模型语境；不能将 Marble 的全部能力归给 Lux3D。[OpenStax Psychology 2e §5.3](https://openstax.org/books/psychology-2e/pages/5-3-vision)介绍透视、遮挡和相对大小等单眼深度线索。[Saund 与 Berenson，PMLR 155（2021）](https://proceedings.mlr.press/v155/saund21a.html)研究不完整深度图的多种合理形状补全，会议为 CoRL 2020；它同时说明机器人可以利用补全几何，不能据此声称机器人只能看二维。

## 实验数字各自说明什么

| 数字 | 原始来源 | 适用范围 |
| --- | --- | --- |
| R1：80.87 秒碰撞、142.20 秒停车、112.84 秒到达 | [R1 执行记录](reviews/RESULT_BEFORESTEP_R1.md)、[逐项 facts](../evidence/production-v6/facts.json) | 原窄道的乐观、保守、Lux3D 三策略仿真时钟；恢复黑影深度的 see-dark 对照也到达，不能说只有两种选择。 |
| 12 世界完整预演；最小三维间隙 47.541 mm | [原报告](report.md) | 六份 A × 两份 B；三维接触几何距离，二维矩形包络间隙为 0 mm，不能写成保证 5 cm 安全余量。 |
| 被拒候选反事实 17/102 碰撞；准入候选 23/64 背面短超过 5 cm | [R2 结果](reviews/RESULT_BEFORESTEP_R2.md)、[逐项 facts](../evidence/production-v6/facts.json) | 前者为原批策略干预次数，后者为赛后几何诊断份数；不是统一样本分母。观测核对和多世界预演通过仍可能实际碰撞。 |
| 最终修订已知 12 场：3 到达、9 停车、0 碰撞；指定留出 5 场：0 到达、5 停车、0 碰撞 | [R3 方法比较](reviews/R3-method-tables.md)、[R3 结果](reviews/RESULT_BEFORESTEP_R3.md) | 合计 3 到达、14 停车、0 碰撞；安全结果伴随通行能力下降。原方法与早期修订碰撞继续保留。 |
| 轮行 0/90、逐轮跨越 24/24 干净通过 | [轮腿结束报告](reviews/RESULT_WHEELLEG_CROSSING_FINAL.md)、[校准记录](../evidence/crossing/calibration/gate.json) | 10、12、15 cm 三个离散高度的冻结 Go2W 仿真条件；未验证其间所有高度、任意底盘或 M20 实机。 |
| 低门槛生成 7/53 准入 | [低石开发说明](crossing.md)、[原低石记录](../evidence/crossing/route/low-stone.json) | 六轮输入开发的累计任务，原十二场正式门槛测试已取消；不能当作正式通行成功率。可见低门槛交给轮腿，未知高石几何由假设支持绕行。 |

四个同路示例中，两场 D 到达且 A 卡住支持腿的作用，但 B 也到达。[原四车结果](reviews/RESULT_WHEELLEG_CROSSING_FINAL.md)完整保留，不能据此证明 Lux3D 在所有场景都必要。

## 491 与 467 是两个统计节点

- [production-v6/facts.json](../evidence/production-v6/facts.json)的 `/lux/live_ledger_counts` 为累计 **491 创建、460 成功 GLB、31 失败**，并保留后续任务号与来源身份。
- [route/lux-usage.json](../evidence/crossing/route/lux-usage.json)为归档节点 **467 创建、438 成功、29 失败**，也是 V5 原稿的统计身份。
- 上传、轮询、预演世界和游戏局数均不计为新的生成任务；本轮只更新展示，没有新增生成或训练。

## 当前试玩与历史研究分别标识

当前试玩的四站是观测、局部想象、预测、探索四个交互阶段。原照片和生成候选复用已有资产，当前相机补看用于本局真实射线观测；初判后手控独立开放，辅助路线需要完成当前选集的全部预演。

启动默认 A:C2 与 B:C1 为一世界；加入同图 A:C1 后为两世界；原 R1 十二世界是另列的研究证据。[实际玩法](mission.md)与[原片和两端整局验收](../evidence/judges-demo/README.md)可逐项复查。

[云深处 M20 公开模型](https://github.com/DeepRoboticsLab/deep_robotics_model/tree/main/M20)已经适配为试玩显示外观；原 Go2W 动力学、碰撞和控制保持。首页轮腿照片取自真实试玩原片，显示外观与研究校准数据分别标明，不能当作 M20 动力学或实机结果。手机只完成触屏模拟，尚未测量真机性能。

月面低斜阳与部分深度缺失是当前仿真观测设定。它们是研究场景，不能扩展为所有月面传感器必然失效或人类空间判断无条件准确。
