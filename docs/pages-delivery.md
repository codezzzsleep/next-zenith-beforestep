# 网站素材的固定版本加载

GitHub Pages 的部署包有 1 GB 大小限制。网站的原模型、输入与研究记录同时保存在主仓库；部署包中重复的 `assets/` 与 `evidence/` 素材改用主仓库固定提交的直链。

构建脚本 `tools/beforestep_mission/offload_pages_assets.py` 逐个核对 Pages 副本与主仓库的 Git blob 或 LFS SHA-256，只有字节相同的副本才进入外链列表。原始主仓库文件保持不变。相对资源引用、动态读取与模型图片由同一份固定版本映射解析，模型陈列室、版本对比、原实验与下载仍可查阅。

机器人 WASM、任务碰撞世界、显示网格、核心页面与回放运行数据继续随站点发布。大型原素材按需加载；不改变模型几何、输入像素、实验阈值、结果或机器人控制。

在拥有两条 Git 历史的本地库中生成可检查的交付稿：

```sh
python tools/beforestep_mission/offload_pages_assets.py \
  --repo . --source-commit <保留原件的main提交> \
  --pages-commit <优化前的Pages提交> --output /tmp/beforestep-pages-delivery
```

输出包含逐 SHA 保留清单 `delivery.json`、准确的部署副本清单 `offloaded-paths.txt`、引用解析器和派生 HTML。脚本只读原仓库；发布时在隔离 Pages 工作树中采用这些文件，删除对应部署副本并提交，不删除主仓库原件。
