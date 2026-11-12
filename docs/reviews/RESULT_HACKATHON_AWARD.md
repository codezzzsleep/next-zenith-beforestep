# RESULT_HACKATHON_AWARD

执行规格：[SPEC_HACKATHON_AWARD.md](SPEC_HACKATHON_AWARD.md)。以负责人执行中更新的原件为准；此前执行记录保留在[历史记录](history/RESULT_HACKATHON_AWARD-before-owner-homepage.md)。R1/R2预注册主结果与冻结证据不变，R3永远标为赛后修订。

最新第二版 SPEC 已交付 `/root/3d/homepage/`，按 C1–C8 顺序执行。首页设计与文案原样集成，真人测试仍由负责人安排。此前 P1–P6 工作和核验继续保留。

| 项目 | 当前状态 | 已实施、实核结果与证据 |
| --- | --- | --- |
| 前置：磁盘/会话/后台恢复 | 完成 | 已按授权删除 `/root/rush`；原会话与实验终态已恢复，不重建已知任务。无在跑实验。 |
| R3实验与完整保全 | 完成；最新技术报告公网核验继续 | 最终v3已知12场：3到达/9停车/0碰撞；留出5场：0到达/5停车/0碰撞。新增拒绝干预：已知17/0碰撞、留出112/13碰撞。完整tar/公开清单与独立origin核验已保全。 |
| P1网页素材包与技术报告搬迁 | 素材公开/本地搬迁完成；首页待负责人交付 | 306真实网页版模型、526索引文件、521配准上下文；最大GLB 1999920字节。锚点12请求/11返回模型/8准入/3拒绝/1供应商失败、四完整轨迹、十二完整预演、每眼RGB/depth/DARK、真值与矩阵齐全。逐SHA、原几何、矩阵及轨迹实核通过；main `7cb3096` 已实际push，独立origin下载500对象/691547326字节，全部pointer SHA与size通过。[远端核验](../../evidence/award/acceptance/web-assets-origin.json)。全部526索引文件实际Pages下载/757640298字节全部SHA与size匹配。[Pages素材实核](../../evidence/award/acceptance/web-assets-pages.json)。[index](../../evidence/web-assets/index.json) · [核验](../../evidence/award/acceptance/web-assets.json)。原首页按原字节与路径接通搬到 `site/report.html`，PDF源另存 `site/project-report.html`。 |
| P1首页集成 | 等待制作方交付 | 已实现 `ops/integrate_owner_homepage.py`，仅接通 `assets/`→`home-assets/`，model-viewer与仓库vendored字节相同；尚未替换正式首页。交付后做1440/390全页截图、模型/拖动/首屏时间/数字/公网验收。真人测试按负责人最新指令不由Agent跟进。 |
| P2结果、回放、技术流程 | 技术报告/结果/关卡/沙盒公网通过；新增失败章发布继续 | 十二已知五栏与五指定留出单表、眼数/仿真时间并列、oldv2碰撞与最终v3范围、十二逐关修订回放、Lux核心工程链数字均齐全。R1/R2与R3数字审计、本地技术页/修订页通过。新版首页交付后原样接通相应入口。 |
| P3补充演示 | 未开始；执行前置条件未满足 | 固定原提交 `f00a08f` 的 `suite_r2_v4_F0_006` 不更换；[原计划](../../evidence/award/demo/plan.json)与[新版28次上限修订](../../evidence/award/demo/budget-amendment.json)均保留。累计R2+R3=288，本项最多新增28/累计316，平台360；当前新增0。P1/P2在11/15 12:00北京时间前完成才执行，不提前伪造完成marker，也不提前写时间跳过。单列“赛后补充演示运行，不参与结论、不作为泛化证据”。 |
| P4报告/PDF/英文摘要 | 本地完成；新增失败章/PDF发布继续 | V6/V7/V8/v0.1/v0.2/v0.3真实模型、冻结配置、原输入SHA与真实截图；失败章前置，新增两次指定留出原想象碰撞的逐任务背面误差、全部预演与实际接触说明。PDF 22页/2203164字节，七原输入SHA与关键文字实际提取通过。英文按已知/留出分层，并列原想象与修订收益和碰撞边界。[PDF实核](../../evidence/award/acceptance/pdf.json)。 |
| P5视频素材 | 完成 | 19素材索引SHA通过，90/45秒分镜每镜来源实在，主线真实照片→整石→转背面，影子只静态短背景。原分镜保留history。真实无头 `--reuse-lux` 终端与8081站点两入口；既有完整真实重用链五轨迹数组与R1精确相同、0新付费。Agent未编码Demo，最终成片由负责人制作。[素材](../../evidence/video/award/index.json)。 |
| P6传播与提交 | Agent材料完成 | 两版小红书文案、八真实配图、标签与公开要求、魔搭模型/Notebook说明与GPU核验说明；提交表逐项有链接/负责人状态/核验时间。[传播材料](../award-promotion.md) · [提交表](../hackathon-submission.md)。视频成片、社交发布、赛事提交由负责人完成。 |
| §11验收 | 独立部分本地与公网通过；新版首页待集成，新增失败章发布继续 | 88unit通过；五R1回归源/数组同，3995保护diff空/323核心SHA实核；R1/R2/R3数字、410文档链接、PDF与19视频素材SHA通过。首页未交付，故不把旧版首页测试冒充新版首屏通过。 |

## 保留的边界

- 原锚点三维间隙47.541mm/二维包络0；原F1_020与F3_004碰撞、oldv2 F1_003碰撞始终保留。
- 原被拒反事实17/102、R3已知0/17与留出13/112分组，次数不冒充独立想象资产份数。
- 原已知决定性想象3到达/3停车/2碰撞；留出原想象1到达/2停车/2碰撞，最终v3修订0到达/5停车/0碰撞。想象有效，但不绝对；修订消掉碰撞的同时消掉留出中的到达收益。
- 视频、帖子与比赛发布由负责人执行；准备好的素材不冒充新视频成片或已提交。

## 下一具体步骤

main `7cb3096`、全部素材LFS与独立origin核验已通过；Pages `2508c35` 已built，技术报告/修订五栏/关卡全部候选/沙盒公网通过。新增留出失败章与22页PDF发布继续；首页成品交付后只接通资产路径并验收。P1/P2正式完成且满足时间条件后，按既有固定计划运行唯一P3演示并完整公开六栏/反事实/保全。

## 第二版 C1–C8 执行记录

| 项目 | 状态与实际验收 | 证据 |
| --- | --- | --- |
| C1 本地集成、数据管线、数字审计 | 原样仅映射路径，11 模型均实际加载；1440/390全页、真实指针拖背面、拒绝文案、三车/两想象切换通过，0溢出/0console/0HTTP。首屏3.6094383979798295秒。7293数据字段相同，14组数字无未解释项。公网发布待验。 | [本地验收](../../evidence/award/acceptance/home-C1-local.json) · [数字审计](../../evidence/award/acceptance/home-numbers.json) · `ops/build_home_data.py` |
| C1 公网发布 | main `d5f8150` 已推送，Pages `90bb13d` built/error null。公网重复1440/390整页、11GLB加载、实际拖背面、全部切换与拒绝文案全部通过；首屏3.96917208598461秒，0溢出/0报错。C1完成。 | [公网验收](../../evidence/award/acceptance/home-C1-public.json) |
| C2 想象陈列室 | 本地完成：306模型全部可查，306封面逐份原SHA/实际loaded/旋转验证；20场景分组、四筛选/任务搜索/实际指针旋转/390无溢出/0error，首屏GLB请求0。全目录330真实任务、110通过/196拒绝/30被拒会撞；231次干预单列，与gallery/facts.json一致，原facts仍按原R1/R2范围。 | [浏览器验收](../../evidence/award/acceptance/C2-gallery-local.json) · [数据](../../site/data/gallery.json) · [封面](../../evidence/web-assets/gallery/posters/index.json) |
| C3 全站统一外观 | 四页使用首页令牌/字体/顶栏/页脚；全部原链接保留，JS只改颜色，数据不动。既有关卡全部12/三选择/模型/计分、沙盒编辑/导出、技术报告9运行/11模型/12预演及20训练回放均通过；390无溢出，0资源错误。 | [不变性](../../evidence/award/acceptance/theme-invariance.json) · [关卡](../../evidence/award/acceptance/C3-levels.json) · [沙盒](../../evidence/award/acceptance/C3-sandbox.json) · [报告](../../evidence/award/acceptance/C3-report.json) |
| C4 真假叠合 | 27GLB均≤2000000字节，原配准/世界坐标、琥珀0.35与灰蓝；在与back-error相同冻结5cm投影上，全部误差差≤5cm。连续顶点投影有3例超5cm（stress B/A2、F3_006 T1/B1/B2），原因是原候选映射到5cm格中心，而真值用凸包包含格中心，两端离散误差合计；原连续值保留，不移动模型或修改实验数字。连续几何的“全部≤5cm”没有通过，不冒充通过。 | [27份叠合/两种投影](../../evidence/web-assets/overlays/index.json) · [原连续验收](../../evidence/web-assets/overlays/history/continuous-first-check.json) |
| C6 单份检查器 | 只读原测量并重算五个冻结门卫，11份锚点与生产逐项一致（8准入）；11项单测实际通过。不是重新测量几何，不改src或原证据。 | [逐份复核](../../evidence/award/acceptance/C6-checker.json) · [单测](../../evidence/award/acceptance/C6-checker-tests.log) · `ops/check_candidate.py` |
| C3 最终四页外观验收 | 训练页行动来源栏初检出现36px移动溢出，已用CSS移动网格与文本折行修复；四页1440/390全页、实际颜色/字体/顶栏/页脚全部通过，0HTTP/console，真实C1-C3 marker在最终检查后更新。 | [四页最终验收](../../evidence/award/acceptance/C3-theme-local.json) |
