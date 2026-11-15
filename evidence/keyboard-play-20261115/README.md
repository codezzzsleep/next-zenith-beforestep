# 月面任务：键盘试玩录像

[观看／下载录像](https://media.githubusercontent.com/media/codezzzsleep/next-zenith-beforestep/main/evidence/keyboard-play-20261115/BeforeStep-keyboard-mission.mp4) · [亲自试玩](https://codezzzsleep.github.io/next-zenith-beforestep/play.html?v=mission-2)

所选高石 A/A1 与 B/A2、B/C1 构成两个模型世界，完整预演通过后，玩家用键盘沿画面路线绕过两块高石。到门槛前，相机测得可见的高度和深度，再预演跨越；玩家依次触发四条腿的 12 个抬起、前移、落地动作，最后恢复轮行并停进绿色终点圈。

录像使用公开网页的 MuJoCo 仿真。原 Lux3D 候选构成可碰撞的模型预演世界；跨越控制器辅助重心和支撑，玩家通过 1–4 选腿、J/K/L 触发主要动作。绕行使用 W/A/D，观察点的导航交接和回到轮行使用界面按钮。

影片长 28 分 32.7 秒，1440×1100、20fps、H.264，无音轨。只裁去接管前的准备和结束后的静止尾段，驾驶、等候与腿部动作保持原速。

完整解码验证通过，末帧确认抵达，动作计数 12/12、四轮过线 4/4。文件大小、SHA-256 与源版本见 [manifest.json](manifest.json)。
