# 先见一步 · Lux3D 核心 Demo

[下载完整 Demo](https://media.githubusercontent.com/media/codezzzsleep/next-zenith-beforestep/main/evidence/lux3d-demo/BeforeStep-Lux3D-Demo.mp4) · [视频与报告 ZIP](https://media.githubusercontent.com/media/codezzzsleep/next-zenith-beforestep/main/evidence/lux3d-demo/BeforeStep-Lux3D-submission.zip) · [正式报告](https://codezzzsleep.github.io/next-zenith-beforestep/media/report.pdf)

![照片与真实模型](BeforeStep-Lux3D-Demo.jpg)

完整成片 157.03 秒（2 分 37 秒），1920×1080、30 fps、H.264、AAC 中文配音、烧录中文字幕。主线是**照片 → Lux3D 生成 3D → 核对 → 路线预演 → 机器人行动**。

同一任务 5958685 的原照片和返回 GLB 并排展示，随后用官方 Aholo Viewer 录屏旋转查看背面。模型参与可见面核对、完整物理预演与实际路线决策。所有运动来自 MuJoCo 原运行回放，片中已注明；候选不可信时停车，也保留模型背面偏短的边界。

真实 Lux3D 任务 491 个，返回 460 份模型，31 次服务端失败。新剪辑没有新增 Lux3D 或物理运行。原 3 分 05 秒故事版与全部 39 条镜头继续保留在 [production-v6](../production-v6/README.md)。

参赛表单的“Demo / 视频链接”可填写上方 MP4 直链，或下载后选择“上传视频文件”。项目报告为原 10 页 v3 PDF，包含过程、输入和核心版本资产对比；同包保留原字节。

[同稿](narration.md) · [镜头表](CUT_LIST.md) · [时间与输入来源](plan.json) · [整片验证](verification.json) · [实际一倍播放](playback.json) · [制作代码](../../tools/lux3d_demo/README.md) · [逐 SHA 清单](MANIFEST.json)
