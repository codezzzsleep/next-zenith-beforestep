"""Explainable visual selection from declared information relationships.
This is a design policy, not a universal numerical law. Source meaning wins over thresholds.
"""
import argparse,json
from pathlib import Path

RELATIONS={
 'comparison':('类别比较','hbar / bar / dot'),
 'trend':('时间趋势','line / area'),
 'composition':('部分与整体','stacked100 / donut'),
 'distribution':('样本分布','histogram / box'),
 'relationship':('两变量关系','scatter'),
 'uncertainty':('区间与不确定性','range'),
 'change':('前后变化或增减构成','slope / waterfall'),
 'conversion':('阶段转化','funnel'),
 'matrix':('多对象多维度比较','matrix / heatmap'),
 'process':('顺序、分支与交接','process / diagram'),
 'hierarchy':('层级与归属','layers / diagram.tree'),
 'network':('系统连接与依赖','diagram.architecture'),
 'chronology':('时间事件与阶段','timeline / roadmap'),
 'schedule':('任务起止与并行','gantt'),
 'lookup':('精确查阅与说明','table / definitions / p')}

def choose(d):
    r=d['relation'];n=d.get('items',0);series=d.get('series',1);alts=[];why=''
    if r not in RELATIONS:raise ValueError('未知 relation；可选 '+', '.join(RELATIONS))
    if r=='comparison':
        kind='hbar' if n>6 or d.get('long_labels') else 'bar';alts=['dot','table'];why='同口径数值比较；长标签或多类别优先横条，精确查值保留表格'
        if series>1:kind='grouped' if series<=4 else 'table';why+='；多系列需共同量纲，超过 4 条优先分面或表格'
    elif r=='trend':
        kind='line';alts=['table','area'];why='横轴必须有真实时间或连续顺序；有缺测则断开，不伪造点'
        if not d.get('has_time'):kind='table';why='未提供时间或连续顺序，不能连线制造趋势'
    elif r=='composition':
        if not d.get('same_total_definition'):kind='table';why='没有共同整体与同一统计口径，先用表格说明'
        else:kind='donut' if 2<=n<=5 and series==1 else 'stacked100';why='单整体少量部分可用环图；多个整体用百分比堆叠，保留分母'
        alts=['stacked','table']
    elif r=='distribution':
        kind='box' if d.get('groups',1)>1 else 'histogram';alts=['scatter','table'];why='分布需要原始样本或完整的统计摘要，只有均值不能画箱线图'
        if not d.get('raw_samples'):kind='table';why='缺少原始样本或可核对的分布统计，保留现有摘要'
    elif r=='relationship':kind='scatter';alts=['table'];why='每个点必须有配对的 x/y 数值；相关关系不写成因果关系'
    elif r=='uncertainty':kind='range';alts=['table'];why='必须注明区间来自最小最大、分位数、置信区间或其他明确口径'
    elif r=='change':kind='waterfall' if d.get('additive') else 'slope';alts=['delta','table'];why='可加总增减项用瀑布；同口径前后两点用斜率；只有一对数可用 delta'
    elif r=='conversion':kind='funnel' if d.get('sequential_subset') else 'bar';alts=['table'];why='只有连续阶段、后项来自前项子集时用漏斗；否则是普通类别比较'
    elif r=='matrix':
        kind='heatmap' if d.get('all_numeric') and d.get('same_scale') else 'matrix';alts=['table','grouped'];why='2–6 个对象、3–8 个共同维度；定性/混合值用矩阵，同量纲纯数值才用热图，不自行打分'
    elif r=='process':
        if d.get('branches') or d.get('loops'):kind='diagram.flow';why='分支或回路的拓扑关系比步骤数更重要；复杂回路单列子图'
        elif n<=3:kind='list';why='2–3 个简单动作使用编号列表即可'
        elif n<=7:kind='process';why='4–7 步使用清晰的线性流程；超过 4 步默认纵向'
        else:kind='process+subflows';why='超过 7 步或单步长说明：先分 3–5 个阶段，再分图展示子步骤，完整说明保留'
        if d.get('roles',1)>=2:kind='diagram.swimlane';why='两个及以上角色有实际交接时优先泳道；仅分工清单用表格'
        alts=['list','diagram.flow']
    elif r=='hierarchy':kind='layers' if d.get('layered') else 'diagram.tree';alts=['definitions','table'];why='表达从属与层次；没有时间或流向，不加流程箭头'
    elif r=='network':kind='diagram.architecture';alts=['layers','table'];why='仅画材料声明的连接与依赖；单图超过 12 节点优先总览加子图'
    elif r=='chronology':
        if not d.get('has_time'):kind='roadmap';why='只有阶段没有日期时用路线图，不能编造时间'
        elif n<3:kind='definitions';why='1–2 个事件直接列出日期与说明'
        else:kind='timeline-horizontal' if n<=5 and not d.get('long_labels') else 'timeline';why='3–5 个短节点可横排；6–10 个或说明较长用纵向；更多按时期分组'
        alts=['timeline','roadmap','table']
    elif r=='schedule':kind='gantt' if d.get('start_end') else 'roadmap';alts=['timeline','table'];why='任务有真实起止且要看并行/工期时用甘特；无起止日期则保留阶段计划'
    else:kind='table';alts=['definitions','p'];why='精确数字、条款、规格与预算应可直接查阅；文字不必强行可视化'
    if d.get('numeric') is False and kind in ('bar','hbar','dot','grouped','line','area','stacked','stacked100','donut','scatter','range','waterfall','funnel','heatmap','histogram','box'):
        kind='matrix' if r in ('comparison','matrix') else 'p';why+='；当前无可用数值，禁止编造图表'
    return {'relation':r,'chosen':kind,'alternatives':alts,'reason':why,'thresholds_are':'可按阅读任务、素材质量、标签长度调整的排版默认值，不是数据事实'}

def cover(d):
    if d.get('preferred'):kind=d['preferred'];why='用户已指定构图，素材条件冲突时调整构图或说明缺项'
    elif d.get('images',0)>=2 and d.get('complementary'):kind='mosaic';why='有多张互补素材，适合呈现多面产出'
    elif d.get('verified_metrics',0) in (1,2,3) and d.get('data_is_thesis'):kind='numbers';why='可靠数据本身就是开篇主张'
    elif d.get('image_orientation')=='portrait':kind='split';why='纵向物体或人物适合与文字并置'
    elif d.get('image_orientation')=='landscape':kind='horizon';why='横向场景需要保留空间关系'
    elif d.get('strong_visual'):kind='poster';why='强主视觉可以承担开篇意象'
    elif d.get('archival'):kind='frame';why='档案、文化或机构语境适合框景与题签'
    else:kind='type';why='没有可靠主图或关键数字时，使用字体与信息层级建立封面'
    return {'chosen':'cover.'+kind,'alternatives':['cover.type','cover.split','cover.horizon'],'reason':why}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('input');ap.add_argument('--cover',action='store_true');a=ap.parse_args();d=json.loads(Path(a.input).read_text());print(json.dumps(cover(d) if a.cover else choose(d),ensure_ascii=False,indent=2))
