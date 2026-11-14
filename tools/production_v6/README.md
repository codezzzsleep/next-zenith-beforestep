# v6 视频与渲染制作代码

这里保留实际制作 v6 的配音、剪辑、字幕、验证、GPU 显示回放与图表处理代码。仓库位置、输出目录和浏览器查找改为可配置路径；原源码 SHA 与公开副本 SHA 见 [source-code-manifest.json](../../evidence/production-v6/source-code-manifest.json)。物理控制、自检阈值和原运行结果没有改动。

最终文件、39 条原镜头及输入数据在 [production-v6](../../evidence/production-v6/README.md)。生成结果的 RPC/SSH 传输和机器灾备配置保留在私有操作环境，不属于这里的渲染、物理或剪辑算法。

## 读取原始数据

在仓库根执行。只下载这个归档，不拉全部历史 LFS 数据：

```bash
git lfs pull --include="evidence/production-v6/**" --exclude=""
python3 tools/production_v6/restore_inputs.py --verify-only
python3 tools/production_v6/restore_inputs.py
```

两个 ZIP 包分别保存正式 F3_002 四车全记录、观测、原候选与 491 条任务缓存，以及全部镜头真正读取的地形、机器人、轨迹与预演依赖。解包逐文件核对 SHA，已存在且不同的文件不会被覆盖。它不执行物理或调用 API。

## 用已交付素材重建视频

Python 3.12、numpy、Pillow、ffmpeg（libx264/libass）和文泉驿正黑字体。配音已缓存，重建无需 MiniMax 密钥、Lux3D 或 GPU。

```bash
python3 tools/production_v6/film/compose.py --phase all
python3 tools/production_v6/film/correct_title.py
python3 tools/production_v6/film/verify_package.py --phase verify
```

脚本先读取已有配音的真实时长，按保存镜头变速或保持终态；三车使用共同回放时钟、取最近的已有编码帧。中间件为无损编码，最终 1080p30、H.264 CRF14 slow、中文烧录字幕、AAC，无配乐和锐化。`correct_title.py` 只修正录屏页头，在关键帧边界拼接并逐帧验证其他区域未变。

可选的浏览器检查需要 Playwright 与 Chromium：

```bash
python3 -m playwright install chromium
python3 tools/production_v6/film/check_playback.py
```

需要重新合成中文配音时才配置自己的 `MINIMAX_API_KEY` 并显式运行 `film/synthesize.py`。缓存任务先核身份与 SHA；不重复成功或未知请求。发布归档不含任何密钥。

## 保存状态的 GPU 回放

使用 NVIDIA EGL、MuJoCo 3.17.0、numpy、Pillow、trimesh、scipy。h-center 参数固定，4K RGB 直接送入 ffmpeg 后一次 Lanczos 缩至 1080p。`gpu-render/bootstrap.py` 禁止 `mj_step`、`mj_step1`、`mj_step2`；回放只设置保存的 23 维 qpos。

```bash
MUJOCO_GL=egl python3 tools/production_v6/gpu-render/render_shot.py --shot s09-connect-overview-v2
```

已有成片会按 SHA 跳过。渲染使用原地形数组和网格，不重新生成地形或调用 Lux3D。质量门卫保留原 CPU/GPU 差异指标与负责人放行证据；原放行对应 RTX 4090 D，原渲染机系统盘已用空间须不超过 20 GB。

实际物理与 Lux3D 主流程仍是仓库原有 `src/beforestep/` 和 `ops/crossing_route_*.py`；新增 F3_002 沿用冻结规则，未增加场景特判。旧版本、候选与失败记录继续保留。

本次 F3_002 的日期编排原源码保留在 [history](history/README.md)。恢复与重建会写入工作副本，请在自己的克隆中操作；正式源文件及已交付视频仍由 Git/LFS 保留。
