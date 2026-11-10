# RESULT_BEFORESTEP_R2

执行规格：[SPEC_BEFORESTEP_R2.md](SPEC_BEFORESTEP_R2.md)。R1仍有效，R2只扩展B/C/D范围。

| 小项 | 内容 | 进度 | 提交 |
| --- | --- | --- | --- |
| A1 | 重验单测、资产SHA、链接、R1数字 | 完成 | 800ef64；发布回执见本提交 |
| A2 | 修重复status并本地浏览器验收 | 完成 | 800ef64；发布回执见本提交 |
| A3 | R1五条结论审计 | 完成 | 800ef64；发布回执见本提交 |
| A4 | R1报告PDF | 完成 | 800ef64；发布回执见本提交 |
| A5 | main/Pages发布及公网验收 | 完成 | 800ef64；发布回执见本提交 |
| A6 | R1结果收尾 | 完成 | 800ef64；发布回执见本提交 |
| B1 | 地形/太阳配置与完整回归 | 进行中 | — |
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

旧失败中第二个status来自model-viewer的Shadow DOM辅助状态。正文回放状态改唯一`run-status`，同步JS与验收定位，不改src。预期9运行、11GLB、12画廊、三历史场景、20训练回放、390px无溢出且无HTTP/页面错误；通过后生成PDF并再次核对所有结论。

A2首次新验收exit1（`outputs/qa/r2/A2-local-browser.log`）：status定位已通过，时间断言把Python整数浮点104.0与浏览器104字符串比较；改为解析秒数并按原summary精确数值比较，保留初失败，不改展示数值或实验。

A2第二次新验收exit1（corrected日志）：9运行及11GLB均已走到链接核验；Playwright穿透三维库Shadow DOM抓到内部javascript链接，HTTP探测因此报协议错误。链接改为首页light DOM中用户实际链接，仍全部HTTP检查，未删正文链接。

A2最终exit0：`python3 ops/check_r1_browser.py --name r2-A2-local-final --pdf`（相同PYTHONPATH），全部9运行、11真实GLB、12预演画廊、3个历史场景、20学习回放通过；正文状态唯一，390px无横向溢出，图片加载，页面与HTTP错误均0。结果：`evidence/reviews/beforestep_r1/presentation/local-browser.json`；截图留`outputs/qa/r1/r2-A2-local-final-{desktop,mobile,report-mobile}.png`。

A3 `python3 ops/verify_r1_presentation.py` exit0，首页/报告五项口径保持：0/3碰撞与偏保守、47.541mm和XY0、真实一眼与第二眼/6b/B替换未触发、B251px/native_ok=false仍两准入、1223.6s含冷配准/预演不含云排队非端到端、旧gate/改终点/训练为未证必要性的附录。数字结果公开在presentation/numbers.json。

A4通过同一真实Chromium打印报告到`site/media/report.pdf`（1.6MB，未渲染视频），原v0.3 PDF保持在`site/media/history/trained_gate_v03/report.pdf`。PDF读取补验见后文。

A5进行中：main准备提交全部R1网页/报告；Pages导出保留所有当前与历史入口引用的GLB，未引用重复网格只从导出剔除，main资产不变。导出246MB/1160文件，完整数据仍在main。实际配额API只读查询404，凭证缺user scope；本阶段无新增LFS对象（site新增为图片/PDF），不扩权限、不把配额可见性当停工。B入库将按§2.5采取保守精简集+外部完整tar，先检查可用性。

A1–A4与R1正文提交`800ef64`，`git push origin main` exit0，远端main同SHA。A4补验Python pypdf读取5页/1625235bytes，关键结论全部在PDF，SHA ae4ceacbc684b4a681cacee2f19442d80fb3f096e70666e5865a0f4574fb5f87。旧系统未安装pdfinfo/pdftotext，首次调用exit127，改用仅本机临时依赖pypdf补验通过，未改项目运行依赖。Pages提交`49eddf8d51893aca091a4d1ff0f07133c870e3e6`推送exit0，构建中；真实公网验收待构建完成。`git diff --name-only src config`为空。

### 阶段 A 小结（§8格式）

1. 完成并验证：规格/进度0a595b5、网页/报告/本地验收800ef64860566241af11b3f312c848f533b82bc9，远端main同800ef64；Pages49eddf8d51893aca091a4d1ff0f07133c870e3e6构建built/error=null，Actions42829258154 success。`python3 ops/check_r1_browser.py --url https://codezzzsleep.github.io/next-zenith-beforestep/ --name r2-A5-public` exit0，9回放、11GLB、12画廊、3历史场景、20训练回放、390px及全部图片/链接通过，HTTP/页面0错误；公网PDF/视频/数据SHA与本地相同。全部40单测、323资产SHA、139链接和数字审计exit0，PDF5页关键结论补验通过。日志`outputs/qa/r2/A1/`、`A2-local-browser-final.log`、`A5-public-browser.log`；公开摘要`evidence/reviews/beforestep_r1/presentation/`。
2. 做了未验证：无阶段A项遗留。
3. 未完成或失败：初status、时间字符串、Shadow DOM链接与依赖调用失败均已修正；初日志保留。新Demo由负责人制作，保留位置/历史视频，不是本轮自渲染待办。
4. 自决：正文状态独立id；网页只检查light DOM用户链接；时间按summary数值比较；历史资产保留；源码/config零改动。三个时间关口尚未到，不提前收缩。
5. 新增Lux3D任务0，R2累计0/360，旧12个任务不重复创建。
6. 提交前仅本回执改动；无实验/生成作业，本地HTTP8081为验收服务，非实验。
7. 下一第一个动作：B1实现可选terrain/sun配置（缺省完全复现旧值），补单测并跑stress_v8四基线与R1全数组复用回归。

## 阶段 B

### B1 实施前决策与运行预期

可选格式：terrain.type=`corridor|plain`，terrain.craters为`{center:[x,y],radius,depth}`列表，terrain.right_wall布尔；sun.elevation_deg/azimuth_deg。缺省为旧窄道、无坑、有右石堆、10°/35°，四份旧配置原字节保留。月坑为轨道已知禁行区，物理高度场下凹，prior_nogo包含坑沿5cm，车不下坑。旧stress_v8按名字关闭参照预演的历史分支需保留旧效果，改为配置性选项并记录缺省兼容理由，不改变执行预演。地形可视缓存按地形参数SHA隔离，旧默认仍原缓存名保证渲染字节一致。

新实验前预期：stress_v8保守stuck、see_dark arrived、乐观collision、truth arrived；R1 reuse全部t/qpos/phase/actions/sources数组完全相同；全部单测通过。不符合先修，不带不一致进入B2。
