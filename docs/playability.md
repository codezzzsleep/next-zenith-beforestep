# 月面任务：边开边学，也能完整挑战

当前主报告为 [V5 Beta](../reports/README.md)，主宣传视频是作者已经发布的 B站片
`https://www.bilibili.com/video/BV1YZst6eEZk/`（BV1YZst6eEZk）。当前玩法与验收见[月面任务](mission.md)和[评审试玩](judges-demo.md)；V3/V4 原件和历史影片继续保存。

打开 `play.html` 即可驾驶。任务现在有四个明确阶段：驶到高石观察点并转看完整模型，
绕过两块高石，在门槛前亲手完成四腿的抬、迈、落，最后驶入目标圈停稳。
第一、第三、俯视和画中画仍来自同一实时物理状态。真实场景保持完整原材质，认知地图只消费真实观测和明确标注的候选假设。初判后自主选择手控、想象、补看或停车，辅助路线受完整预演许可约束。

## 两种模式

- **探索练习**：机器人在高石观察点、门槛整备点和跨越后的实际停稳位置保存检查点。
  按 R、结果卡上的继续按钮或任务面板，可以回到最近检查点，继续尝试。
- **全程挑战**：从起点一次完成。每次重新开始重置本轮成绩，个人纪录保留；不使用练习检查点。

“换组真实模型开新局”依次轮换已经准入的高石 A 原模型，并加入两份已准入 B 模型。它与初始评审选择不同：初始为 A:C2 加固定 B:C1 的一世界，同图比较加入 A:C1 后为两世界；换组的实际组合数量由新选集决定。
当前所选几何重新参与占据规划和模型世界预演。这个入口只复用实际返回，
不会改变月面真值、降低准入门槛或创建生成任务。玩家仍可主动比较和调整候选。

## 局内成绩与勘察印记

局内积分最多 100 分：抵达 40，四腿 12 个主要动作完成 20，实际试路后沿认证路线出发 20，
主动转看两块高石的原模型 10，抵达且最大倾角不超过 8° 再得 10。
还有先见一步、四腿接力、两面勘察、稳稳到达、亲手领航和一气呵成六枚印记。

成绩来自实际 worker 事件、实时位置/倾角和玩家主动转面动作。未完成或取消的试路不计为
认证路线；失败不写成完成纪录。行动仿真用时只累计实时驾驶及腿部运动，停看、暂停和
脑内试路不计。探索练习与全程挑战分别保存，纪录只留在本机；复制成绩由玩家主动点击。
这些积分是新增游戏规则，与赛事评分和原 R1/R2/R3 科学实验分别计数。

## 检查点的实际含义

`mission-worker.js` 保存自己的停稳物理快照。恢复属于明确的重置：销毁当前腿控制器，
复制保存的 qpos/qvel 和电机姿态目标，再继续 MuJoCo 求解。正常驾驶与跨越仍全部来自
原 16 个执行器的力矩。客户端不能提供恢复位姿。

恢复会取消当前预演、推进选择修订、清空路线和门槛认证。恢复高石观察点后先按该检查点的初判状态选择下一步；
手控独立开放，重新使用辅助路线要重新完整试路。界面只恢复检查点当时已经观察到的表面，后续看到的
背面不会提前带回旧观察点。检查点继续次数出现在结果卡中，不冒充连续完整运行。

## 源码与检查

局内事实、成绩和本机纪录在 `site/mission-run.js`；任务面板和提示在
`site/mission-gameplay.js`；检查点由原实时 worker 管理。
`site/mission-scene.js` 增加已知任务目标的金色标记，标记不参与物理求解。

```sh
node tools/beforestep_mission/check_playability.mjs /tmp/playability.json
node tools/beforestep_mission/check_playability_worker.mjs /tmp/playability-worker.json
node tools/beforestep_mission/check_experience.mjs /tmp/experience.json
node tools/beforestep_mission/check_showcase.mjs /tmp/showcase.json
python3 tools/beforestep_mission/check_gameplay_browser.py \
  --url https://codezzzsleep.github.io/next-zenith-beforestep \
  --output /tmp/beforestep-gameplay/result.json --full
```

浏览器检查需要 Playwright/Chromium，Node 检查复用随站点保留的 WASM 与物理资产。
完整浏览器检查只操作按键、鼠标/触屏；不注入物理状态，不重新录制主宣传片。
新增字符使用原 V3 Noto 字体的小补充子集，原三份 WOFF2 字节保持；构建器和固定来源
见 `tools/beforestep_mission/build_playability_fonts.py`、`site/fonts/gameplay-provenance.json`。

手机验收使用 Chromium 的实际触屏事件模拟，真实手机性能仍需单独测量。
真实模型符合观测、所选模型预演通过，仍不保证未知背面正确。
