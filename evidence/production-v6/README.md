# BeforeStep · v6 成片、全部镜头与数据

[直接下载 3 分 05 秒成片](https://media.githubusercontent.com/media/codezzzsleep/next-zenith-beforestep/main/evidence/production-v6/demo-v6.mp4) · [下载成片压缩包](https://media.githubusercontent.com/media/codezzzsleep/next-zenith-beforestep/main/evidence/production-v6/BeforeStep-demo-v6.zip) · [39 条原素材](shots/) · [制作代码](../../tools/production_v6/README.md)

![v6 成片封面](demo-v6.jpg)

成片 185 秒、1920×1080、30 fps，MiniMax 中文配音与烧录字幕同稿，H.264 CRF14 slow、AAC，无配乐或锐化。完整解码 5550 帧、35 代表画面及实际播放/9 处跳转已通过。完整文件 SHA：`0e878e89f672bdf966be88a46de07407101a953f3b6ec27e86de5ccc8d4f99d2`。

| 内容 | 入口 |
| --- | --- |
| 当前成片、VTT 和封面 | [MP4](demo-v6.mp4)、[VTT](demo-v6.zh.vtt)、[封面](demo-v6.jpg) |
| 所有原版/v2/gate/备用/ACT5 镜头与网页录屏 | [39 条镜头](shots/)、[镜头索引](shots/index.json) |
| 第五幕连接回放与停车镜头 | [ACT5 清单](shots/ACT5_SHOTS.md) |
| 同稿、剪辑与时间映射 | [配音稿](film/narration.md)、[镜头表](film/CUT_LIST.md)、[时间映射](film/timeline.json) |
| 来源事实、正式四车终态 | [事实](facts.json)、[F3_002 结果](gate-result.md) |
| F3_002 的完整轨迹、观测、自检、原候选、任务缓存 | [原始数据 ZIP](data/F3_002-terminal.zip)、[逐文件 SHA](data/F3_002-terminal.manifest.json) |
| 镜头读取的机器人/地形/纹理/原轨迹及预演依赖 | [渲染输入 ZIP](data/render-inputs.zip)、[逐文件 SHA](data/render-inputs.manifest.json) |
| 最终画面与播放验证 | [验片](film/verification.json)、[画面](film/visual-review.json)、[播放](film/playback.json) |
| 页头修正前的成片 | [首版留档](history/demo-v6-before-title-fix.mp4)、[500 帧修正与 5050 帧原样验证](film/title-correction.json) |
| 原图与渲染参数对照 | [报告图](figures/)、[单变量渲染对照](render-ab/)、[GPU 一致性](gpu-render/gpu-consistency.json) |

所有运动画面都是原 MuJoCo 运行保存状态的回放；模型与页面素材来自已有实际产物和浏览器录屏。没有新物理、Lux3D 任务或站点发布。

第五幕的连接片属于使用真实形状的连接预检查，不能计为正式 D 或 Lux3D 到达成绩。正式 F3_002 的 A/D 都在高石段停车，门槛段未发生；B 因轮触高石由原监视器停车，机身未触石。A/D 的完整第一段 NPZ 和八个数组相同。

同路五场中，有腿的想象车 D 到达两场。新 F3_002 在前四场结果之后追加，是单场演示，不是统计证据。当前 Lux3D 总计 491 次真实创建、460 份 GLB、31 次服务端失败；旧 467/438/29 保留为补充 4 前的历史基线。

`r01-reveal` 为原公开叠合页面的事后诊断；`r04-photo-to-glb` 复用旧录屏。它们的来源限制保留在镜头元数据中。旧成片与未选用镜头不覆盖。

二进制由 Git LFS 保存。只需观看成片时可使用上方直接下载链接；需要完整归档时运行：

```bash
git lfs pull --include="evidence/production-v6/**" --exclude=""
```

[MANIFEST.json](MANIFEST.json) 记录公开副本与原文件的 SHA。视频、轨迹、观测和原模型按原字节保留；元数据路径为仓库相对路径。凭据、机器私有记忆、SSH 会话和编码中间件不进入归档。
