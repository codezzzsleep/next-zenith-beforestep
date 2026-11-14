# 决定 B2：渲染参数终版 + 改用 GPU 机（负责人 Claude，2026-11-14 23:00 北京时间）

取代 `DECISION_B.md` 与 `SPEC_RENDER_CNB.md` 中的渲染参数与机器分工。CNB 那台没有显卡，**不再使用**。

## 1. 参数：采用 H，再加 2 倍超采样

依据：同一帧（`leg` 第 2857 行）白壳框内孤立黑点数 / 亮度≥250 的像素占比。

| 方案 | 黑点 | 过曝 | 结论 |
| --- | --- | --- | --- |
| leg-e | 12 | 3.3% | 不用 |
| leg-g-clip / leg-h-center | 7 / 7 | 4.2% | **采用 h-center** |
| leg-i-fill | 2 | 13.2% | 过曝超过 5% 上限，白壳发平，不用 |
| leg-j-2x（带补光） | 0 | 12.6% | 同上，不用 |

最终渲染参数 = `h-center`：1920×1080 原生，`shadowsize` 8192，`offsamples` 4，`shadowclip` 3，`znear` 0.001，阴影中心跟随机器人，**无补光**。在此之上，用 3840×2160 渲染再用 lanczos 一次缩到 1920×1080（GPU 上代价可以忽略）。不加任何锐化滤镜。

## 2. 机器

- 渲染机：操作者自己的 NVIDIA GPU 主机；连接参数不进入公开归档。
- 已装好：`/root/deps`（MuJoCo 3.17.0、numpy、pillow、trimesh、scipy、matplotlib，用 `PYTHONPATH=/root/deps`）、libEGL、ffmpeg（含 libx264、h264_nvenc、subtitles 滤镜）、WenQuanYi Zen Hei 字体。
- EGL 已用 NVIDIA：设 `MUJOCO_GL=egl`，`GL_RENDERER` 应显示 RTX 4090 D。一个 1080p 简单场景 0.0018 秒/帧。
- 限制：系统盘只有 28GB。素材渲出来马上压成 mp4，不要囤 PNG 序列。pypi 官方与 GitHub 连不上，装包用 `-i https://pypi.tuna.tsinghua.edu.cn/simple`。
- 用完要关机（按小时计费）。

## 3. 做什么（按顺序）

1. **打最小渲染包并推过去**。从 Vultr 列出 §3 全部镜头真正读取的文件，只拷这些：各镜头的 `trajectory.npz`/`traj.npz`、场景定义 JSON、地形与石头 mesh、机器人 XML 与 mesh、纹理、`src/beforestep/visualization`、`ops/crossing_real_footage_capture.py`、`visual-review-v5/photography.py`、`final-v6/render_ab.py`、`final-v6/common.py`。用 `rsync -e "ssh -p 39139"` 推到 GPU 机的 `/root/render-v6/`。
2. **一致性检验**：在 GPU 机上用 `h-center` 参数（不超采样）渲 `leg` 第 2857 行，与 Vultr `render-ab/leg-h-center-clean.png` 比较，把最大差、平均差、不同像素占比写进 STATUS。几何与阴影形状应一致，最大差 ≤ 8（GPU 与软件光栅的舍入会有小差）；超了就把差异图放 `render-ab/gpu-diff.png` 停下等我。
3. **批量渲 §3 全部镜头**，包括 `s09-gate-*`（等 F3_002 终态再渲，数据从 Vultr 取）。先渲一个镜头，把实测每帧耗时写进 STATUS。
4. **回传**：**帧不落盘**。渲染进程把每帧的 RGB 字节直接写进 `ffmpeg` 的标准输入（`-f rawvideo -pixel_format rgb24 -video_size 3840x2160 -framerate 30 -i pipe:0`，滤镜 `scale=1920:1080:flags=lanczos`，`-c:v libx264 -crf 14 -preset slow -pix_fmt yuv420p`，不烧字）。`visual-review-v5/capture.py` 里已有同样的管道写法，照用。原因：GPU 机系统盘只有 28GB，1080p PNG 全部落盘约 10GB，4K 约 31GB，会撑爆。除一致性检验的 2 到 3 张对照图外，不得保存 PNG 序列。每个镜头输出 mp4 后推回 Vultr `final-v6/shots/`，校验 SHA256 一致。
5. **STATUS**：每步追加一行。全部完成后写一行 `GPU 渲染完成，可关机`，我会告诉用户关机。开始前和结束后各写一行 `df -h /` 的结果，磁盘用量超过 20GB 就停下排查。

## 4. 不变

太阳方向、传感器输入、23 维状态、物理结果、冻结源码一律不动。GPU 机上不跑物理、不调 Lux3D、不放任何密钥。
