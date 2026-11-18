# README 与首页图文来源

当前 README 使用真实月面试玩截图和三张 1600×900 的原研究证据图，首页采用同一组图片。原观测、原模型、十二世界和运行终态均按原来源取材，图片只按比例缩放并拼版。

| 文件 | 内容 |
| --- | --- |
| `../../site/media/home-evidence-20261118/01-observation-and-candidates.jpg` | 同一眼 RGB 原图，任务 5958654 通过、5958642 被拒，原轮廓核对数值 |
| `../../site/media/home-evidence-20261118/02-twelve-world-rehearsals.jpg` | `s05-world-grid.mp4` 第 3 秒的完整四乘三十二格 |
| `../../site/media/home-evidence-20261118/03-three-real-outcomes.jpg` | R1 三策略同步原片第 40.5 秒，独立标注仿真终态时间 |
| `../../site/media/game-spatial-imagination-preview-20261118.jpg` | 当前 M20 外观、原生成模型与局部空间路线的实际试玩截图 |

原任务、输入与视频 SHA、时间码和输出尺寸见[三图来源](../../site/media/home-evidence-20261118/sources.json)。三策略使用原 Go2W 条件，当前试玩截图使用 M20 显示外观；两者的来源不混写。

## 重制当前证据图

需要 Pillow、ffmpeg 与 CJK 字体，不运行仿真或生成新模型。拉取源图与原片后执行：

```sh
python docs/readme/build_evidence_panels.py   --repo . --world-grid evidence/production-v6/shots/s05-world-grid.mp4   --font /path/to/NotoSansCJKsc-Bold.otf
```

`--source-root` 可指定拥有原二进制文件的另一份本地工作副本；脚本仍以源 SHA 和原任务身份核对素材。

## 保留的历史 README 资产

`photo-to-model.gif`、`model-to-decision.png`、`viewer.jpg`、`robot-action.jpg` 与 `asset-iterations.png` 均保留，原来源在[sources.json](sources.json)。原四步流程图使用当时的素材节点，当前首页和 README 已采用完整十二世界的新三图。

历史图文的重制工具是 [build_assets.py](build_assets.py)，其原影片为 `evidence/lux3d-demo-v2/BeforeStep-Lux3D-Demo-v2.mp4`。不要用旧构建器的输出覆盖当前证据图目录。
