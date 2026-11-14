# 配乐与动画修订的实际制作代码

prepare_audio.py 复用原旁白，截取已下载的 Fluidscape，动态压低背景音并首尾渐变。motion.py 使用已有真实照片和录屏像素做17处演示过渡。render.py 流式解码原片并合成，字幕带保留原帧；verify.py 和 check_playback.py 验完整解码、声音与真实播放。没有Lux3D、物理或TTS调用。

原主片、输入照片与原23句缓存在 evidence/lux3d-demo；新音乐原字节前缀、原旁白WAV、已替换片尾两句的旁白WAV、两句新缓存、配乐署名和混音/动画计划在 evidence/lux3d-demo-v2。重做只复用缓存，不新调TTS。请先拉取相应Git LFS实体。代码依赖Python、Pillow、NumPy、ffmpeg/ffprobe；浏览器检查另需Playwright和Chromium。

从仓库根目录运行。为保全已交片，用新目录复制music和sources，再以BEFORESTEP_LUX_DEMO_V2_DIR指定该目录，先prepare_audio.py再render.py。完成的视频存在时合成器拒绝覆盖。复现不需要API密钥。

```bash
git lfs pull --include="evidence/lux3d-demo/**,evidence/lux3d-demo-v2/**" --exclude=""
mkdir -p /tmp/beforestep-lux3d-v2-rebuild/qc /tmp/beforestep-lux3d-v2-rebuild/logs
cp -r evidence/lux3d-demo-v2/music evidence/lux3d-demo-v2/sources /tmp/beforestep-lux3d-v2-rebuild/
cp evidence/lux3d-demo-v2/timeline.json /tmp/beforestep-lux3d-v2-rebuild/
BEFORESTEP_LUX_DEMO_V2_DIR=/tmp/beforestep-lux3d-v2-rebuild python tools/lux3d_demo_v2/prepare_audio.py
BEFORESTEP_LUX_DEMO_V2_DIR=/tmp/beforestep-lux3d-v2-rebuild python tools/lux3d_demo_v2/render.py
```

本轮验证实际成片和公开原字节、路径与代码导入；没有另外重编码全片或在新机器重做全部历史实验。
