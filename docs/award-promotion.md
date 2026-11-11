# 传播材料（由负责人发布）

## 小红书：技术版

我做了一台会“先见一步”的月面轮腿机器人：实际 RGB-D → Aholo Lux3D 多候选 → 观测配准与冻结自检 → 完整物理预演 → 独立执行 → 被拒候选反事实。

原批真实生成任务 180 个、GLB 166 份。原窄道 Lux 到达，但预注册场景组也发生两次想象碰撞：一块石头完全藏在视线后，一份背面假设偏短却通过正面自检。原拒绝候选反事实 17/102 碰撞。

后来做了“只解释太阳黑影、继续观察视线未知”的赛后修订。最终 v3 已知场景：3到达、9停车、0碰撞；指定留出：0到达、5停车、0碰撞。 只有固定留出支持样本外判断，停车不是通行成功。所有失败、输入 SHA、任务、GLB、预演和源码保留。

可体验： https://codezzzsleep.github.io/next-zenith-beforestep/levels.html
源码： https://github.com/codezzzsleep/next-zenith-beforestep
报告： https://codezzzsleep.github.io/next-zenith-beforestep/report.html

#Aholo黑客松
发布后至结果公布前保持公开。

## 小红书：大众版

石头挡住路时，你会直接走、多看一眼，还是先想象它看不见的背面？

我把这个问题做成了能玩的月面实验。机器人面对两种影子：太阳照不到的黑影，以及被岩石挡住的视线。移动相机能改变视线，却不能把太阳黑影照亮。它请 Aholo Lux3D 提出背面的几何假设，再走进完整物理预演，最后才行动。

它有走到终点的记录，也有真的撞上石头的记录。好看的假设不等于正确的背面，所以网页把失败原因、所有选择与真实轨迹一起展示。点一个策略，看看你的选择会发生什么。

体验： https://codezzzsleep.github.io/next-zenith-beforestep/
这是实际仿真实验，不是实机演示；赛后修订与补充演示都有单独标注。

#Aholo黑客松
发布后至结果公布前保持公开。

## 配图（真实观测或实际网页截图）

1. [first.png](../evidence/video/award/first.png)
2. [second.png](../evidence/video/award/second.png)
3. [asset-iterations.png](../evidence/video/award/asset-iterations.png)
4. [award-local-desktop-1440.png](../evidence/video/award/award-local-desktop-1440.png)
5. [award-local-two-shadows.png](../evidence/video/award/award-local-two-shadows.png)
6. [award-final-local-choices.png](../evidence/video/award/award-final-local-choices.png)
7. [award-final-local-failures.png](../evidence/video/award/award-final-local-failures.png)
8. [award-final-local-revision.png](../evidence/video/award/award-final-local-revision.png)

## 魔搭社区模型页与 Notebook 文本

项目名：BeforeStep / 先见一步。核心是 Aholo Lux3D 真实几何候选、观测自检、全部采纳世界完整预演与独立执行。模型页同时列出规则导航主实验、历史学习控制权重以及失败证据，历史权重不冒充 R3 的控制器。

Notebook 从公开源码安装，使用已有观测与 Lux 结果复现，不要求读者提供生成密钥。入口依次为环境检查、数据 SHA 核验、已记录场景复用、真实轨迹回放和原失败说明。云端新生成是单独可选流程，需要读者自己的额度；默认复现不创建任务。

仓库：https://github.com/codezzzsleep/next-zenith-beforestep
Demo：https://codezzzsleep.github.io/next-zenith-beforestep/
报告：https://codezzzsleep.github.io/next-zenith-beforestep/report.html
模型权重：仓库 `assets/models/`；任务输入与真实候选：`assets/`；视频素材：`evidence/video/award/`。

活动说明：魔搭社区发布经核验后可获 20 小时 Notebook GPU 额度；这里提供说明文本，未声称已领取。负责人发布后填入模型页链接与 Notebook 链接。

模型页链接：负责人待发布；Notebook链接：负责人待发布。小红书链接：负责人待发布。
