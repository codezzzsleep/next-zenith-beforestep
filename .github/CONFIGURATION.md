# GitHub 项目配置

[repository-settings.json](repository-settings.json)保存仓库简介、主页、主题与当前报告/原片发布入口。源码分支为 `main`，Pages 保留 `gh-pages` 根目录与已有固定素材映射。

文档检查脚本为 [verify_public_delivery.py](../ops/verify_public_delivery.py)，本次已核对原报告 SHA、入口链接、图片尺寸及历史文件身份。

[自动检查模板](workflow-templates/verify-delivery.yml)与[模板说明](workflow-templates/verify-delivery.properties.json)作为可复用配置交付。当前部署沿用已有 Pages 构建；如需启用这份检查，可在拥有工作流管理权限时将模板放入 `.github/workflows/`。

```sh
python3 ops/verify_public_delivery.py
```

检查只读已交付文件和身份，不启动生成、训练或物理实验。当前交付与版本见[状态说明](../docs/current-status.md)。
