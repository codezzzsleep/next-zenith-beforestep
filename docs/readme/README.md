# README 图文素材

首页图文取自项目的机器人观测、Lux3D 返回模型、官方 Aholo Viewer 显示和 MuJoCo 运行画面。

| 文件 | 内容与来源 |
| --- | --- |
| `photo-to-model.gif` | 最新配乐版 Demo 的 4.1–11.9 秒，8 fps、宽 900 px；照片与模型来自任务 5958685 |
| `model-to-decision.png` | 原照片、原模型显示、12 世界预演和机器人行动组成的四步流程图 |
| `viewer.jpg` | 最新 Demo 第 35 秒：官方 Aholo Viewer 查看 Lux3D 模型 |
| `robot-action.jpg` | 最新 Demo 第 84 秒：R1 原运行绕行回放 |
| `asset-iterations.png` | 从[原六版本资产对比图](../../evidence/production-v6/figures/six-version-assets.png)取出实际模型与对应输入，按版本标注技术作用 |
| `badges/*.svg` | Lux3D、官方 Viewer、MuJoCo 在作品中的职责 |

详细源路径、素材摘要和影片版本见 [sources.json](sources.json)。影片是 [BeforeStep-Lux3D-Demo-v2.mp4](../../evidence/lux3d-demo-v2/README.md)，来源提交 `ab537d62c075c4d7be1e829cecb69a4708258221`。

## 重新制作

[build_assets.py](build_assets.py) 从仓库中的相同素材制作 GIF、截图、流程图与职责标记。需要 Python、Pillow、ffmpeg 和文泉驿正黑字体；字体路径也可通过 `--font` 指定。

```bash
git lfs pull --include="evidence/lux3d-demo-v2/**,evidence/production-v6/figures/**" --exclude=""
python docs/readme/build_assets.py --out outputs/readme-assets
```

输出到新目录，便于与已发布图文逐文件比较。
