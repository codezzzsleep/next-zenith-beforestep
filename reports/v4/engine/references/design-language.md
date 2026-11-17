# 设计语言与独立旋钮

将稳定部分固定为色彩角色、字体层级、网格、间距、边框与标注规范。让封面、页面组合与内容结构随材料变化。

## 配色不绑定题材或构图

| palette | 基础气质 | 可作为起点的方向 |
| --- | --- | --- |
| midnight | 午夜蓝、琥珀 | 技术、数据、可信与探索 |
| forest | 墨绿、金色 | 自然、城市、生态与生活 |
| vermilion | 纸色、朱砂 | 文化、教育与出版 |
| graphite | 石墨、信号橙 | 工程、工具、制造 |
| ocean | 深海青、珊瑚 | 公共服务、环境与健康 |
| plum | 紫、玫金 | 设计、内容与消费 |
| terracotta | 陶土、橄榄 | 社区、农业、手作 |
| cobalt | 钴蓝、明黄 | 机构、申报与企业 |
| mono | 黑白、编辑红 | 研究、政策与极简出版 |
| aurora | 极光紫、薄荷 | 年轻产品、互动与实验 |

按项目自己的素材、气质与读者选色，不按行业机械对应。10 个 preset 位于 `design/presets.json`，组合这些独立参数；任何参数可覆盖。例：

```json
{"style":{"preset":"culture-guide","palette":"mono","cover":"type","header":"rail","density":"regular"}}
```

## 旋钮取值

| 参数 | 可选项 | 作用 |
| --- | --- | --- |
| palette | 上表 10 种名称，或完整基础色对象 | 所有组件共用色彩角色 |
| cover | horizon / poster / type / split / numbers / frame / mosaic | 默认封面构图；实际 `cover.kind` 可覆盖 |
| header | kicker / numeral / band / rail / split / minimal | 全册主页头；`pages[].header` 可局部变奏 |
| art | ridges / contours / network / waves / orbits / blocks / halftone | 未指定时的装饰意象；无需每页使用 |
| radius | sharp / soft / round | 边角规则 |
| card | tint / outline / flat / edge | 普通卡片的底色与边框规则 |
| fontpair | serif-sans / sans-sans / serif-serif / mono-accent | 标题、正文、数字与工具字的角色分配 |
| density | compact / regular / airy | 字号与导语层级；不作为删减内容的开关 |
| footer | rule / minimal / index / none | 页底身份与页码 |

6 类页头中，numeral 只在真实章节有顺序时使用；split 只在有一句真实摘要时使用。不要为统一外观给无序内容补序号或补答案。

## 色彩角色

- `paper / ink / mut / line / tint`：纸面、主文、辅助文、分隔与弱容器。
- `accent / accent2`：视觉重点和次级系列，不自动表示成功/失败。
- `good / bad / mid`：结果状态，必须配文字说明。不能把自己的方案自动标为 good。
- `dark / cover`：大面积对比区与封面底色。
- `series`：图表系列色；同一个系列在整份报告中保持同色。

`core.resolve_palette()` 从基础色推导前景、浅底与封面颜色，对主要文字组合调整对比度。它不能替代对照片背景、细字号与叠色场景的目视检查。新增调色板时保留 `paper, ink, mut, line, tint, accent, accent2, good, bad, mid, dark, cover` 等字段，参照 `palettes.json` 的完整对象。

## 排版与节奏

- A4 210×297mm，常规正文有效宽度 180mm，基本页边距 15mm。
- 常规正文 10.3pt，compact 为 9.8pt，airy 为 10.7pt；辅助图注 8.2–8.5pt。自动分页不缩字号。
- 图片常用通栏、1/2 栏或 2/3 栏；重要结构图优先通栏。
- 一页建立一个主要视觉重心，但不是每页强制大数字。可以是标题、真实大图、数据图、矩阵或阅读中的留白。
- 全册通常使用一个主页头、一个主体卡片皮肤、一个调色板；变奏用于章节级差异，而不是逐页随机换风格。
- 保持足够的连续正文。卡片用于分组，不能把每一句话切成同样大小的卡片。

先以主题建立独特性，再检查是否只是换了配色的通用科技模板。改掉一个可以出现在任何项目里的装饰元素，用该项目自己的素材、比例、术语结构或真实产出替代。
