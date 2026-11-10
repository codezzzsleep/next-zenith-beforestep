# RESULT_BEFORESTEP_R2

执行规格：[SPEC_BEFORESTEP_R2.md](SPEC_BEFORESTEP_R2.md)。R1仍有效，R2只扩展B/C/D范围。

| 小项 | 内容 | 进度 | 提交 |
| --- | --- | --- | --- |
| A1 | 重验单测、资产SHA、链接、R1数字 | 完成 | 0a595b5（规格）；回执见后续提交 |
| A2 | 修重复status并本地浏览器验收 | 完成 | 发布提交见后文 |
| A3 | R1五条结论审计 | 完成 | 发布提交见后文 |
| A4 | R1报告PDF | 完成 | 发布提交见后文 |
| A5 | main/Pages发布及公网验收 | 未开始 | — |
| A6 | R1结果收尾 | 未开始 | — |
| B1 | 地形/太阳配置与完整回归 | 未开始 | — |
| B2 | 参数预注册、生成器、候选池分类 | 未开始 | — |
| B3 | 冻结场景组并推送 | 未开始 | — |
| B4 | 四类真实形状替身完整链 | 未开始 | — |
| B5 | 场景组真实Lux3D | 未开始 | — |
| B6 | 全部场景复盘和全部拒绝反事实 | 未开始 | — |
| B7 | 完整总表 | 未开始 | — |
| B8 | 预定规则结论 | 未开始 | — |
| C1 | 五步关卡模式 | 未开始 | — |
| C2 | 沙盒与一致性 | 未开始 | — |
| C3 | 导出与人工场景 | 未开始 | — |
| D1 | 首页/报告/相关工作整合 | 未开始 | — |
| D2 | 全验收和main/Pages发布 | 未开始 | — |

## 当前身份与授权

- 开始：2026-11-10 13:51 UTC；main本地/远端均 `40044b46a060ea6862545502c9f0639aff316225`。实际工作区与规格§1吻合：R1网页/报告半成品未提交，src无改动，无实验作业。
- 12个R1真实任务全部終态，沿用原证据，不重新创建。R2新增付费任务：0；累计0/360。
- 单一执行会话核验：进程/root/3d当前终端为本会话，其余codex终端在/root/dshcli；无第二个本项目执行作业。
- 保持四份场景原字节、机器人/传感器链、admission/protocol与规则控制器；新范围按规格预注册，结果好坏全部保留。

## 阶段 A

### A1 运行前预期

全部单测40项、资产323项SHA、文档链接、R1数字核对均应通过，确认旧记录。原失败日志保留，新日志在 `outputs/qa/r2/A1/`。此阶段不改src、不调用Lux3D。

A1实际：`PYTHONPATH=/tmp/lunar-review-20261109-deps:/tmp/beforestep-browser-deps:src python3 -m unittest discover -s tests -v` exit0，40/40（2.122s）；资产323/323 SHA通过；`python3 ops/check_document_links.py` exit0，16文档/139链接无缺失；同PYTHONPATH执行`python3 ops/verify_r1_presentation.py` exit0，9运行、11候选、12预演轨迹与报告HTML及数字来源通过。日志/JSON：`outputs/qa/r2/A1/`。资产审计首调用误用assets键exit1，修为entries键通过；归档数字核对首调用缺PYTHONPATH导致markdown导入失败exit1，恢复相同依赖路径后通过（corrected日志），未修改证据或src。规格提交0a595b5已推送，远端同SHA。

### A2 运行前预期与修正

旧失败中第二个status来自model-viewer的Shadow DOM辅助状态。正文回放状态改唯一`run-status`，同步JS与验收定位，不改src。预期9运行、11GLB、12画廊、两历史场景、20训练回放、390px无溢出且无HTTP/页面错误；通过后生成PDF并再次核对所有结论。

A2首次新验收exit1（`outputs/qa/r2/A2-local-browser.log`）：status定位已通过，时间断言把Python整数浮点104.0与浏览器104字符串比较；改为解析秒数并按原summary精确数值比较，保留初失败，不改展示数值或实验。

A2第二次新验收exit1（corrected日志）：9运行及11GLB均已走到链接核验；Playwright穿透三维库Shadow DOM抓到内部javascript链接，HTTP探测因此报协议错误。链接改为首页light DOM中用户实际链接，仍全部HTTP检查，未删正文链接。

A2最终exit0：`python3 ops/check_r1_browser.py --name r2-A2-local-final --pdf`（相同PYTHONPATH），全部9运行、11真实GLB、12预演画廊、2个历史场景、20学习回放通过；正文状态唯一，390px无横向溢出，图片加载，页面与HTTP错误均0。结果：`evidence/reviews/beforestep_r1/presentation/local-browser.json`；截图留`outputs/qa/r1/r2-A2-local-final-{desktop,mobile,report-mobile}.png`。

A3 `python3 ops/verify_r1_presentation.py` exit0，首页/报告五项口径保持：0/3碰撞与偏保守、47.541mm和XY0、真实一眼与第二眼/6b/B替换未触发、B251px/native_ok=false仍两准入、1223.6s含冷配准/预演不含云排队非端到端、旧gate/改终点/训练为未证必要性的附录。数字结果公开在presentation/numbers.json。

A4通过同一真实Chromium打印报告到`site/media/report.pdf`（1.6MB，未渲染视频），原v0.3 PDF保持在`site/media/history/trained_gate_v03/report.pdf`。PDF读取补验见后文。

A5进行中：main准备提交全部R1网页/报告；Pages导出保留所有当前与历史入口引用的GLB，未引用重复网格只从导出剔除，main资产不变。导出246MB/1160文件，完整数据仍在main。实际配额API只读查询404，凭证缺user scope；本阶段无新增LFS对象（site新增为图片/PDF），不扩权限、不把配额可见性当停工。B入库将按§2.5采取保守精简集+外部完整tar，先检查可用性。
