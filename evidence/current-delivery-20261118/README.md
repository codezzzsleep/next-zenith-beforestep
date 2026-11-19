# 当前交付、文档与入口核对

本目录记录 2026-11-18 当前 V5 Beta 报告、可玩 Demo、原片、首页证据图和 GitHub 入口的一致性。

[机器可读交付清单](manifest.json)列出当前主报告的 SHA、11 页阅读图、公开入口与受保护历史文件；[文档检查结果](verification/document-checks.json)记录本次实际检查。

首页三图来自保留的原 R1 观测核对、完整十二世界与三策略终态，全部为 1600×900。[原素材与 SHA](../../site/media/home-evidence-20261118/sources.json) · [本地桌面/390px 验证](verification/home-layout.json)。

## 原数据的可点击入口

此前技术报告中 61 个 `run_identity.json` / `eval.json` 链接仍指向已转入 gzip 归档的目录。`review-metadata/` 从公开原压缩对象按原清单逐 SHA 和字节数提取，没有重新计算或创建身份；总计 478,373 字节。原压缩对象继续保留。[原路径、对象与 SHA 对照](restored-links.json)。

当前主报告为负责人上传的 V5 Beta 原件。V3/V4 PDF、六个技术节点、输入、原 GLB、研究规格和结果保持原身份。原片下载的实际核验范围见[原片记录](../judges-demo/verification/public-downloads.json)，不将 API digest 核对写成大文件匿名完整下载已完成。

源码与站点采用普通 `main` / `gh-pages` 发布，保留原 6,448 条固定素材映射。GitHub 简介、主题和当前发布入口与同一交付清单对应。
