# 公开介绍与宣传入口

作者已发布的主宣传片是[B站视频](https://b23.tv/4CAPaLu)，BV1aYsw6REh7。当前主报告为 V5，互动入口为[月面探索](https://codezzzsleep.github.io/next-zenith-beforestep/play.html)。以下文案可供负责人自行使用；本项目没有代发其他社区或代交比赛表。

## 可直接使用的简介

先见一步给机械狗增加空间想象。相机看清石头的一面，Lux3D 生成多份可能的完整形状；BeforeStep 用已有观测核对这些候选，把它们放回局部通道，在候选世界里规划和预演，再决定前进、补看或停车。

你可以亲自驾驶 M20 外观的轮腿机器人：在石缝前留下初判，自选手控、让 Lux3D 想一想、再看一眼或停下。脑内窗口并排展示同图候选、占地和路线，生成模型实际参与碰撞预演。绕过高石后，亲手完成四腿的 12 个主要动作，再驶入信标。

项目真实创建了 400 多次 Lux3D 任务，输入、模型、被拒结果与失败都可复查。原 R1 窄道中，直接走一眼碰撞，补看五眼后停车，Lux3D 与十二世界预演支持一眼、112.84 秒仿真时间到达。其他场景也有碰撞和停车，生成候选与预演不能保证未知背面一定正确。

当前演示与研究均为 MuJoCo 仿真。Lux3D 接收普通 RGB 图片，本地 RGB-D、位姿和地形帮助配准与核对；网页复用已有真实模型，不实时提交当前游戏相机帧。M20 是试玩显示外观，原研究使用 Go2W。跨越低门槛使用已测几何，不能把腿的作用都归于 Lux3D。

## 分享时使用的入口

| 内容 | 链接 |
| --- | --- |
| 作品与试玩 | https://codezzzsleep.github.io/next-zenith-beforestep/ · https://codezzzsleep.github.io/next-zenith-beforestep/play.html |
| 主报告 V5 | https://codezzzsleep.github.io/next-zenith-beforestep/report.html |
| 主宣传视频 | https://b23.tv/4CAPaLu |
| 1080p 原片、五图和剪辑索引 | https://github.com/codezzzsleep/next-zenith-beforestep/releases/tag/judges-demo-20261118 |
| 原模型、源码与失败证据 | https://github.com/codezzzsleep/next-zenith-beforestep |

## 可用真实配图

[受限第一眼](../evidence/judges-demo/figures/01-limited-first-look.jpg)、[同图两候选](../evidence/judges-demo/figures/02-one-photo-two-backs-and-checks.jpg)、[占地与路线](../evidence/judges-demo/figures/03-footprint-and-route.jpg)、[预演决策](../evidence/judges-demo/figures/04-rehearsal-decision.jpg)、[M20 轮腿行动](../evidence/judges-demo/figures/05-M20-leg-action.jpg)。它们是原录制的实际抽帧，身份和时间码见[完整清单](../evidence/judges-demo/manifest.json)。

首页的[三张证据图](../site/media/home-evidence-20261118/sources.json)对应原 R1 观测核对、十二世界和三策略结局。发布时应保留研究与当前试玩的来源标识。

## 社区与 Notebook 文本

模型页可介绍已有学习控制权重和研究附录，当前试玩主线采用冻结规则控制与 MuJoCo WASM。Notebook 复现按 [README](../README.md#本地运行)拉取已有资产并运行 `ops/quickstart.py --reuse-lux`，默认不创建生成任务。

ModelScope、Notebook、小红书与比赛表的实际链接由负责人发布后补入，不从历史草稿推断已发布或已领取额度。最新材料状态见[提交核对](hackathon-submission.md)。
