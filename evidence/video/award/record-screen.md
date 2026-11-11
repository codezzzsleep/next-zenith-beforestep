# 真实运行录屏入口

## 入口一：终端真实无头流程

从仓库根运行下列一条命令。它复用原首眼 Lux 资产，终端打印真实观测、生成任务复用、自检、十二个完整物理预演、独立执行；不产生新付费任务。负责人录制终端。无头运行没有图形窗口，画面来自终端输出与既有离屏帧。

```bash
PYTHONPATH=/tmp/lunar-review-20261109-deps:/tmp/beforestep-browser-deps:src MUJOCO_GL=egl /usr/bin/python3 -u ops/award_record_screen.py --headless --reuse-lux evidence/reviews/beforestep_r1/lux/original_b
```

上述 PYTHONPATH 是本机已核验的依赖目录。在负责人工作站激活 README 的虚拟环境后使用 `MUJOCO_GL=egl python -u ops/award_record_screen.py --headless --reuse-lux evidence/reviews/beforestep_r1/lux/original_b`。每次使用新的输出目录，默认自动以 UTC 时刻命名。既有实际验证见 `evidence/award/acceptance/record-screen-command.json`，完整日志在 `outputs/qa/r3/final/award-record-screen.log`。

## 入口二：站点真实回放与沙盒

本机打开 `http://127.0.0.1:8081/report.html#assets` 录制真实 GLB 的旋转，再打开 `http://127.0.0.1:8081/levels.html` 录制原结果与赛后修订回放，`http://127.0.0.1:8081/sandbox.html` 录制轻量沙盒。也可以运行 `python ops/export_site.py --out /tmp/beforestep-recording-site`，再运行 `python -m http.server 8081 --directory /tmp/beforestep-recording-site`。负责人首页完成集成后，首屏石头录屏入口改用站点 `/`。模型与照片来源是 `evidence/web-assets/anchor.json`，每项带任务 ID 与 SHA。

有桌面/OpenGL 时可将命令的 `MUJOCO_GL=egl` 改成 `glfw` 并去掉 `--headless`，额外观察被动 MuJoCo 窗口。服务器上的无头验证不冒充 GUI 验收。实际传感器重新渲染若与原字节不一致，会保存 NEED_LUX3D 并停止；不加载密钥或自动生成，不用新生成绕过身份核验。

网页轨迹回放与轻量沙盒均有明确标注。新视频由负责人制作，当前旧 mp4 保持历史标识。完整 22 个运行的物理、观测与渲染来源使用 `evidence/video/index.json`，不要从外包代替这些公开数据。
