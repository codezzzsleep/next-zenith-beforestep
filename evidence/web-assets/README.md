# 真实网页素材包

入口是 [index.json](index.json)，逐文件列出路径、SHA-256、字节数、角色与来源任务/证据。模型、观测、配准、轨迹均来自既有真实运行，准备此包不创建生成任务。

- [anchor.json](anchor.json)：stress_v8 的全部生成请求（包括供应商失败）、成功模型（包括被拒）、原上传图、四台车每眼 RGB/深度/DARK、四条完整轨迹、十二个完整预演世界、真值模型与占据。
- [models.json](models.json)：每个实际返回 GLB 的任务、输入 SHA、网页版路径。单个模型不超过 2,000,000 字节。纹理压缩；几何保留原字节。少量仅几何预览保留 float32 三角形位置并明确省略纹理，原始模型未改变。
- [registrations.json](registrations.json)：每个观测上下文的任务、自检全部数值、冻结阈值、准入/拒绝与原因、配准矩阵。相同任务在不同运行复用时，矩阵仍按观测分别记录。
- [facts.json](facts.json)：间隙、背面误差、原场景与赛后修订统计，链接至原证据。已知与留出场景分别报告；真值诊断不作为 Lux3D 成功。

生成 GLB 使用原始 glTF 坐标。真值 GLB 使用世界坐标转 Y-up；叠合时向生成模型应用对应上下文的 `viewer_y_up_from_generated` 矩阵。`world_from_generated` 是工程 Z-up 世界配准，不可与前者混用。矩阵按行存储。

原深度保留 float32 NPY；16-bit PNG 仅为展示，毫米编码，0 表示原 DARK 或远平面背景，65.535m 以上裁剪。DARK 图来自记录标签，不等于纯太阳几何阴影。原始深度与 DARK 分别保留。

本机入口：`http://127.0.0.1:8081/evidence/web-assets/index.json`。公开静态导出保留本目录全部索引资产，原 GLB 与冻结结果仍在仓库既有路径。

核验：从仓库根执行 `python ops/verify_web_assets.py`；[实际核验结果](../award/acceptance/web-assets.json)记录逐文件 SHA、来源字节、压缩前后几何、配准以及完整轨迹检查。
