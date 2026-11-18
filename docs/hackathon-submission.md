# 当前参赛材料核对

核对日期：2026-11-18。当前主报告为 **V5**，主宣传入口使用作者已发布的 B站视频，试玩与原片使用下面固定入口。历史赛程和旧阶段要求保留在原规格中，不作为新的待办时间表。

| 材料 | 当前入口与身份 |
| --- | --- |
| 主报告 V5 | [在线逐页报告](https://codezzzsleep.github.io/next-zenith-beforestep/report.html) · [原文件与版本索引](../reports/README.md) |
| 可运行 Demo | [月面探索](https://codezzzsleep.github.io/next-zenith-beforestep/play.html) · [作品首页](https://codezzzsleep.github.io/next-zenith-beforestep/) |
| 主宣传视频 | [B站](https://b23.tv/4CAPaLu)，BV1aYsw6REh7，作者已上传 |
| 连续 1080p 原片与补拍 | [judges-demo-20261118](https://github.com/codezzzsleep/next-zenith-beforestep/releases/tag/judges-demo-20261118)，约五分钟母片、模型/地图补拍和停车分支 |
| 五张图、研究素材和剪辑时间码 | [原片与图像索引](../evidence/judges-demo/README.md) · [导演素材说明](demo-edit-guide.md) |
| 源码、输入、原 GLB 和真实任务 | [公开仓库](https://github.com/codezzzsleep/next-zenith-beforestep) · [代码导览](code-tour.md) · [核心版本资产比较](../evidence/award/asset-iterations/manifest.json) |
| 研究对照与失败边界 | [R1](reviews/RESULT_BEFORESTEP_R1.md) · [R2](reviews/RESULT_BEFORESTEP_R2.md) · [R3](reviews/RESULT_BEFORESTEP_R3.md) · [轮腿最终结论](reviews/RESULT_WHEELLEG_CROSSING_FINAL.md) |
| 其他社区与比赛表 | [可复用介绍](award-promotion.md)；负责人自行发布和提交，当前不声称已代交 |

## 已验证的实际范围

当前试玩公开入口的桌面与 390×844 触屏模拟各完成六阶段、两世界、12 次玩家动作与真实到达，零页内错误、无姿态注入。模型和占地补拍经原片抽帧检查，地图完整可见，候选标签未遮暗模型。手机真机性能未测。

原视频完成全解码，素材包通过成员 SHA 与 ZIP CRC，六个 Release 附件的 GitHub digest 已核对。四个小附件匿名下载已通过；两个大文件的匿名整文件 GET 校验未完成。固定下载已经存在，实际核验记录在[原片目录](../evidence/judges-demo/README.md)。

原研究使用 Go2W，当前试玩是 M20 显示外观，动力学和控制沿用冻结条件。影片中的研究、候选假设、实时预演与独立执行分别标注。当前默认两世界与原 R1 十二世界分别识别。

导演最终 112 秒片的配音、音乐、字幕与剪辑尚由导演制作，不能将已交付的连续母片称为最终成片。主要宣传继续使用作者 B站片。

## 保留的历史要求

[补充说明 3](reviews/SPEC_WHEELLEG_CROSSING_ADDENDUM3.md) · [旧核对表](history/hackathon-submission-before-addendum3.md) · [原研究规格](reviews/REVIEW_BEFORESTEP_R1.md)。原规格、输入、阈值、任务和报告原件不因文档更新而改写。当前入口与版本见[交付状态](current-status.md)。
