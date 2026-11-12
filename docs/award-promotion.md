# 传播材料（由负责人发布）

## 小红书：技术版

机器人拍到的只是一张平面照片。Aholo Lux3D 把它变成一整块三维石头，包括相机没有看见的那一面。我们让轮腿机器人在多份真实生成的石头旁完整预演，再到独立仿真执行：实际 RGB-D → 多候选 → 冻结自检 → 逐世界预演 → 执行 → 反事实。

原批真实生成任务 180 个、GLB 166 份。原窄道 Lux 到达，但预注册场景组也发生两次想象碰撞：一块石头完全藏在视线后，一份背面假设偏短却通过正面自检。原拒绝候选反事实 17/102 碰撞。

已知决定性 8 场，原想象 3 到达、3 停车、2 碰撞。样本外 5 场，原想象 1 到达、2 停车、2 碰撞；最终 v3 修订 0 到达、5 停车、0 碰撞。Lux3D 让车走到没有想象就走不到的地方，错误的背面也会让车撞上；修订消掉碰撞，同时消掉留出中的到达收益。有效，但不绝对。锚点三维间隙 47.541 mm，二维包络间隙 0 mm，成功不稳健。 oldv2 F1_003 碰撞保留。

可体验： https://codezzzsleep.github.io/next-zenith-beforestep/
全部真实生成： https://codezzzsleep.github.io/next-zenith-beforestep/gallery.html
源码： https://github.com/codezzzsleep/next-zenith-beforestep
报告： https://codezzzsleep.github.io/next-zenith-beforestep/report.html

#Aholo黑客松
发布后至结果公布前保持公开。

## 小红书：大众版

一张照片，能不能想出整块石头？

月面机器人只能拍到石头的一面，却要从背面旁边通过。低角度太阳让背光面全黑，换位置也照不亮。Aholo Lux3D 把实际照片变成可以转动的完整石头；转到背面，那一面是它想出来的。

先转转真实生成的石头，再看机器人怎样核对照片、在每个想象世界里走完整条路。它确实到过，也真的撞过。收紧规则后，样本外的碰撞消失，到达也消失。有效，但不绝对。网页把这些失败与原轨迹一起保留，也有可以玩的关卡。

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

项目名：BeforeStep / 先见一步。一张真实照片变成包含未知背面的完整三维石头。核心是 Aholo Lux3D 真实几何候选、观测自检、全部采纳世界完整预演与独立执行。模型页同时列出规则导航主实验、历史学习控制权重以及失败证据，历史权重不冒充 R3 的控制器。

Notebook 从公开源码安装，按 README 执行 `git lfs install --local`、LFS拉取和依赖安装，再运行 `.venv/bin/python ops/quickstart.py --reuse-lux`，使用已有观测与 Lux 结果复现，不要求读者提供生成密钥。入口依次为环境检查、数据 SHA 核验、已记录场景复用、真实轨迹回放和原失败说明。云端新生成是单独可选流程，需要读者自己的额度；默认复现不创建任务。

仓库：https://github.com/codezzzsleep/next-zenith-beforestep
Demo：https://codezzzsleep.github.io/next-zenith-beforestep/
报告：https://codezzzsleep.github.io/next-zenith-beforestep/report.html
模型权重：仓库 `assets/models/`；任务输入与真实候选：`assets/`；视频素材：`evidence/video/award/`。

活动说明：魔搭社区发布经核验后可获 20 小时 Notebook GPU 额度；这里提供说明文本，未声称已领取。负责人发布后填入模型页链接与 Notebook 链接。

模型页链接：负责人待发布；Notebook链接：负责人待发布。小红书链接：负责人待发布。
