# 四站任务、检查点与完整挑战

本轮按用户要求保持 V3 主报告，以作者已上传的 B站视频
`https://b23.tv/4CAPaLu` 为主宣传入口，增强实际可玩任务。

四站目标、探索练习与全程挑战、真实停稳检查点、换组原模型、局内积分、六枚勘察印记
和本机个人纪录已接入原实时物理链。原 R1/R2/R3、训练、资产、准入与控制器不改写。
规则及复现见 [可玩性说明](../../docs/playability.md)。

## 本轮实际验证

- [局内规则](game-rules.json)：6 项事实/取消/选择变更/纪录边界通过。
- [真实 worker](worker.json)：6 项检查通过，探索重置和完整挑战分别实际跨越并抵达。
- [浏览器](browser.json)：16 项键盘与触屏检查，0 JS 错误。实际碰撞后从检查点继续，
  另从起点完成全程挑战：2 世界预演、12 次玩家主要动作、抵达、6 枚印记、100 分。
- 原 [体验](experience.json)、[必经模型展示](showcase.json) 和 [认证/取消](session.json) 回归通过。
- [字体](fonts.json) 与 [保留核对](retention.json) 通过：323 项原核心资产全 SHA 相同，
  原 V3 PDF、原三份字体、原物理资源与研究源码保持。

积分和行动仿真时间是新增游戏指标，与赛事评分、原研究结果及云生成耗时分别计数。
完整浏览器流程由验收脚本操作实际按键，未注入物理状态。本轮没有重录主宣传片，
手机使用 Chromium 的真实触屏事件模拟，尚未做手机真机性能基准。

## 实际画面

| 画面 | 桌面 | 手机触屏模拟 |
| --- | --- | --- |
| 模式、任务与个人纪录 | [desktop-modes.jpg](desktop-modes.jpg) | [mobile-modes.jpg](mobile-modes.jpg) |
| 带着原 3D 模型手控 | [desktop-manual.jpg](desktop-manual.jpg) | [mobile-manual.jpg](mobile-manual.jpg) |
| 必经模型转面 | 原任务同流程 | [mobile-observation.jpg](mobile-observation.jpg) |
| 实际碰撞后的检查点继续 | [failed-checkpoint.jpg](failed-checkpoint.jpg) | 触屏重置检查通过 |
| 真实完整挑战抵达和成绩 | [challenge-complete.jpg](challenge-complete.jpg) | 本轮未做完整手机通关 |

[B站主入口](bilibili-primary.jpg) · [总验收](verification.json) · [源码 SHA](source-sha.json) · [本目录字节清单](manifest.json)
