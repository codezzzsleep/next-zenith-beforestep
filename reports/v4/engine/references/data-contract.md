# 输入与输出数据契约

目录：spec；页面；组件；inventory；facts；chart；diagram；命令与产物。

## spec.json：最小外壳

```json
{
  "version":2,
  "document":{"title":"项目名","mode":"compose","audience":"评审","allow_rewrite":false},
  "style":{"preset":"research","palette":"mono","cover":"type"},
  "cover":{"kind":"type","title":"项目名","subtitle":"作品策划案"},
  "facts":[],
  "pages":[{"id":"context","title":"项目背景","blocks":[{"type":"p","text":"用户提供的真实材料。"}]}]
}
```

- `version` 固定为 2；旧 HTML 模板不是新版本输入。
- `document.mode`：`compose` 新组稿；`reflow` 重排已有文件，必须提供已核对的 inventory。
- `inventory`：JSON 对象或相对于 spec 的台账路径；台账图片路径相对于台账文件。
- `facts`：事实数组或 JSON 文件路径。空数组不证明没有遗漏数字，应另核对材料。
- `cover` 可选；没有封面也可生成正文。`kind` 覆盖 `style.cover`。它被转换成一个整页组件。
- `seed` 默认为 7，控制程序插画；相同请求可复现视觉形态。
- 所有图片路径相对于 spec；绝对路径也可。先下载并核对外部图片，生成过程不抓取远程 URL。

## pages：自由组合，不是章节槽位

常规页：

```json
{"id":"method","title":"方法与条件","kicker":"METHOD","header":"rail","number":"02",
 "lead":"可选导语。","blocks":[{"type":"process","items":[{"title":"输入","text":"说明。"},{"title":"输出","text":"说明。"}]}]}
```

整页构图：

```json
{"id":"opening","component":{"type":"page.statement","title":"一句真实主张","text":"已有材料中的解释。"}}
```

`id` 唯一，字母开头，使用字母/数字/下划线/连字符。`title/kicker/header/number/lead/answer` 都不是每页必填项。`blocks` 数量自由。目录组件用 `target` 指向逻辑页 ID，自动续页不会让目录指向错误位置。

不要在一张普通页中嵌套 `cover.*`、`page.*`。不要给所有页面强加数字章号。长主题可连续多页。

## 原子组件

执行 `python3 scripts/catalog.py --kind text` 等命令查询字段；类别为 `cover/header/page/layout/text/number/card/figure/structure/time/table`。`example` 是实际可运行的输入形状，示例值不是项目事实。

常见组合：

```json
{"type":"row","ratios":[2,1],"items":[
 {"type":"image","src":"img/screen.png","caption":"真实运行截图。","fit":"contain","height":65},
 {"type":"stack","blocks":[{"type":"heading","text":"图中要点"},{"type":"p","text":"完整解释。"}]}
]}
```

普通文字可使用安全行内标记：`**加粗**`、`==强调==`、反引号代码、`[[g:通过]]` 等状态文字。输入中的 HTML 被转义。`source` 原文块不解释这些标记，按原字显示。`\n` 显示换行。

每个普通块可附 `fact_ids`。改写块可附 `source_ids` 与 `rewrite_note`。这些字段只声明追踪关系；不能用一串 ID 代替原文内容。

## inventory.json：信息单元账本

```json
{"version":1,"inventory_reviewed":true,
 "source":{"filename":"来源.pdf","sha256":"原文件哈希","pages":2},
 "units":[
  {"id":"u1","kind":"text","text":"原始段落，含全部限定条件。","source":"来源.pdf","page":1,"required":true},
  {"id":"u2","kind":"image","asset":"source-assets/figure.png","text":"原图图注。","source":"来源.pdf","page":2,"required":true}
 ]}
```

使用 `{"type":"source","ids":["u1","u2"]}` 输出对应原文和原图。一个单元出现一次；自动续页时引擎会记录完整片段，不重复或截断。不要手动编辑引擎生成的 `fragments` 来伪装完整性。

`source.py` 输出 `inventory_reviewed=false`，附原页参考图和提取警告。必须逐页审查后才能改为 true。原页参考图不自动当成新报告的整页背景；它用于核对尚未提取的矢量图和表格。需要保留的图应补成独立 image 单元。

`required=false` 只用于有明确处理依据的装饰单元等，仍会在审计中产生警告，且不会豁免源单元覆盖检查。未经授权不能用它隐藏未保留的正文。授权省略写 `omissions:[{"id":"u1","reason":"用户明确要求略去……","user_authorized":true}]`，只有确实获得授权才可填写 true。

## facts：数值与状态

```json
[{"id":"sample","display":"24 份","context":"测试样本数，不代表整体可靠性",
  "source":"用户材料第 3 页","status":"observed"}]
```

状态为 `observed / planned / estimated`。图表或正文通过 `fact_ids:["sample"]` 引用。`display` 要与 PDF 的可见表示一致，不带行内标记。原始值、单位、时间、样本和口径在 context 或原材料里保留。已用事实的显示值会在生成后的 PDF 文本中核对；未引用的数值不会因此自动得到验证。

## chart.data：18 种精确 SVG

通用分类/系列（bar、hbar、grouped、stacked、stacked100、line、area、dot、slope、donut、waterfall、funnel）：

```json
{"kind":"bar","labels":["甲","乙"],"unit":"份",
 "series":[{"name":"样本数","values":[12,18]}]}
```

包在 `{"type":"chart","title":"标题","data":{...},"source":"实际出处","takeaway":"可选且有依据的解读"}` 中。`source` 必填。所有值为有限数；各系列与 labels 等长。分类硬上限 24，系列硬上限 6；实际建议更少，超出先分图。

| kind | 数据字段 |
| --- | --- |
| scatter | `points:[{x,y,size?}]`；`x_unit/y_unit`；size 为非负量，面积与 size 成正比；`size_scale` 可选 |
| histogram | `samples:[数值]`；`bins` 为箱数或明确箱边界数组；默认 auto；`unit` 标测量量纲 |
| box | `groups:[{name,values:[原始样本]}]`；`unit` |
| heatmap | `rows:[标签]`、`columns:[标签]`、`values:[[数值]]`、`unit`；每格维度一致 |
| gantt | `tasks:[{name,start:"YYYY-MM-DD",end:"YYYY-MM-DD",milestone?:true}]`；end 不早于 start |
| range | `items:[{label,low,value,high}]`；`interval_label` 必填，说明给定区间口径 |

`slope` 的 labels 必须只有两个时点；donut 2–6 部分且总和 >0；stacked100 每类总和 >0；funnel 不接受负数或数值上升。程序无法仅凭递减数值证明漏斗语义，应先核对实际阶段关系。

脚本目前不接收 `null` 缺测值；将缺测前后拆成独立线段/图，并用文字保留缺测事实，禁止补零或插值冒充观测。需要对数轴、真正不规则时间间隔、置信带、地理投影或其他未实现的科学图时，使用外部精确绘图工具，按统一字体与配色导入原图；不要把未支持的选项写进 JSON 假装生效。

`charts.sample(kind)` 仅供画廊与测试。正式文档不得用它填补数据。

## diagram.data：五种拓扑图

```json
{"kind":"flow",
 "nodes":[{"id":"a","label":"收到材料"},{"id":"b","label":"资料完整？","shape":"decision"},{"id":"c","label":"进入设计","key":true}],
 "edges":[{"from":"a","to":"b"},{"from":"b","to":"c","label":"是"}]}
```

- `kind`：`flow / tree / architecture / swimlane / cycle`。
- 声明的边才会绘制；节点 ID 唯一，端点必须存在。
- 普通 flow/tree/architecture 按有向无环图布局。复杂反馈回路分离成子图；不要把回边删除后仍声称展示了完整流程。
- `swimlane`：额外给 `lanes:[角色名]`，每个节点给 `lane`；最多 4 道，按拓扑顺序布局。
- `cycle`：3–8 节点，edges 必须按 nodes 顺序形成一个完整闭环。
- 单图最多 16 节点、同层最多 4 节点；长标签会增高节点，无省略号截断。大图可能超过单页，需按关系拆图。

## 生成命令与产物

```bash
python3 scripts/charts.py chart.json chart.svg --palette forest
python3 scripts/diagram.py topology.json topology.svg --palette mono
python3 scripts/art.py --demo 插画目录 forest
python3 scripts/engine.py spec.json report.pdf
```

引擎输出 PDF、自包含 HTML、最终分页 spec、审计 JSON 和联系表 JPG。`*.pages.json` 是可追踪的最终组装结果，不是内容摘要。不要把其中的内部审计字段写进用户的项目正文。
