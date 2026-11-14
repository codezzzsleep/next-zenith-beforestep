# Lux3D 核心 Demo 的实际制作代码

compose.py 将保留的原镜头、原输入和原始模型录屏与同稿音频组合；verify.py 检查整片解码、字幕、声画时长和 SHA；check_playback.py 在 Chromium 完整一倍播放并检查跳转。没有物理运行、Lux3D 或 TTS API 调用，23 句已生成配音缓存随交付保存。

先拉取 `evidence/lux3d-demo/**` 和 `evidence/production-v6/**` 的 Git LFS 实体。输入依赖与逐 SHA 在 `evidence/lux3d-demo/plan.json`；Pillow、ffmpeg/ffprobe 为合成依赖，浏览器验收还需 Playwright 与 Chromium。所有命令从仓库根目录执行。

为保留已有成片，在新目录复用计划与缓存，再以 `BEFORESTEP_LUX_DEMO_DIR` 指定该目录运行 compose.py。原成片路径存在时，合成器会拒绝覆盖；不需要 API 密钥。

```bash
git lfs pull --include="evidence/lux3d-demo/**,evidence/production-v6/**" --exclude=""
mkdir -p /tmp/beforestep-lux3d-rebuild
cp evidence/lux3d-demo/plan.json evidence/lux3d-demo/state.json /tmp/beforestep-lux3d-rebuild/
cp -r evidence/lux3d-demo/audio /tmp/beforestep-lux3d-rebuild/
BEFORESTEP_LUX_DEMO_DIR=/tmp/beforestep-lux3d-rebuild python tools/lux3d_demo/compose.py
```

本次完成文件/来源/配音 SHA 校验、可移植计划读取、整片解码和真实浏览器播放；没有另做一次完整新编码来宣称独立复现。
