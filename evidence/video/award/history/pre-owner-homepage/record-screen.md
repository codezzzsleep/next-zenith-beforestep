# 真实运行录屏入口

在有桌面的本机或负责人工作站，安装仓库依赖并从仓库根运行。此命令复用原首眼 Lux 资产，重新自检、完整物理预演与独立执行，不创建付费任务，也不编码 Demo。网页与 MuJoCo 被动查看器分别打开，负责人录屏。

```bash
PYTHONPATH=/tmp/lunar-review-20261109-deps:/tmp/beforestep-browser-deps:src MUJOCO_GL=glfw /usr/bin/python3 ops/award_record_screen.py
```

上述 PYTHONPATH 是本机已经核验的依赖目录；在负责人工作站激活 README 的虚拟环境后使用 `MUJOCO_GL=glfw python ops/award_record_screen.py`。每次使用新的输出目录，默认自动以 UTC 时刻命名。

`--headless` 用于无桌面验证实际重用链；录屏时省略它。GUI 需要桌面/OpenGL，服务器上无 DISPLAY 的验证不冒充 GUI 验收。实际传感器重新渲染若与原字节不一致，会保存 NEED_LUX3D 并停止；该命令不加载密钥或自动生成，不能用新生成绕过身份核验。

网页轨迹回放与轻量沙盒均有明确标注。新视频由负责人制作，当前旧 mp4 保持历史标识。完整 22 个运行的物理、观测与渲染来源使用 `evidence/video/index.json`，不要从外包代替这些公开数据。
