"""18 SVG chart types, semantic input validation, no fabricated sample data.

CLI: python3 scripts/charts.py request.json out.svg --palette forest
Common: {kind, labels, series:[{name,values}], unit?}. See references/data-contract.md.
"""
import argparse,json,math,datetime as dt
from pathlib import Path
import numpy as np
from core import resolve_palette, mix, on_color, wrap
from svg import Canvas,num,fmt,scale,extent

KINDS=('bar','hbar','grouped','stacked','stacked100','line','area','dot','slope','donut','scatter','histogram','box','heatmap','gantt','waterfall','funnel','range')

def sample(kind):
    d={'kind':kind,'labels':['甲','乙','丙','丁'],'series':[{'name':'系列 A（示例）','values':[12,24,18,30]}],'unit':'份'}
    if kind in ('grouped','stacked','stacked100','line','area','slope'):d['series'].append({'name':'系列 B（示例）','values':[18,16,26,22]})
    if kind in ('line','area'):d['labels']=['第 1 期','第 2 期','第 3 期','第 4 期']
    if kind=='slope':d['labels']=['之前','之后'];[s.update(values=s['values'][:2]) for s in d['series']]
    if kind=='donut':d['labels']=['甲','乙','丙'];d['series'][0]['values']=[45,30,25]
    if kind=='scatter':d={'kind':kind,'points':[{'x':1,'y':3},{'x':2,'y':4},{'x':3,'y':2},{'x':4,'y':6}], 'x_unit':'输入量','y_unit':'输出量'}
    if kind=='histogram':d={'kind':kind,'samples':[1,1,2,2,2,3,4,5,6,8,9,10],'bins':5,'unit':'测量值'}
    if kind=='box':d={'kind':kind,'groups':[{'name':'甲','values':[1,2,3,4,8,12]},{'name':'乙','values':[2,4,6,8,9,10]}],'unit':'测量值'}
    if kind=='heatmap':d={'kind':kind,'rows':['甲','乙','丙'],'columns':['指标一','指标二','指标三'],'values':[[12,24,36],[8,16,24],[6,18,30]],'unit':'分'}
    if kind=='gantt':d={'kind':kind,'tasks':[{'name':'调研','start':'2027-01-01','end':'2027-01-08'},{'name':'原型','start':'2027-01-05','end':'2027-01-18'},{'name':'评审','start':'2027-01-20','end':'2027-01-20','milestone':True}]}
    if kind=='waterfall':d['series'][0]['values']=[40,20,-10,15]
    if kind=='funnel':d['series'][0]['values']=[120,90,60,30]
    if kind=='range':d={'kind':kind,'items':[{'label':'甲','low':10,'value':15,'high':22},{'label':'乙','low':14,'value':20,'high':28}],'unit':'测量值','interval_label':'原材料给定区间'}
    return d

def _series(d):
    labels=d['labels']; series=d['series']
    if not labels or not series or len(series)>6:raise ValueError('需要分类标签与 1–6 条系列；更多系列请分面')
    for s in series:
        if len(s['values'])!=len(labels):raise ValueError('每条系列与 labels 必须等长')
        for v in s['values']:num(v)
    return labels,series

def make(d,pal=None,width=900,height=430):
    p=pal or resolve_palette('midnight'); k=d['kind']
    if k not in KINDS:raise ValueError(f'未知图表 {k}；可选 {KINDS}')
    colors=p['series']; w=width; h=height; unit=d.get('unit','')
    if k in ('bar','hbar','grouped','stacked','stacked100','line','area','dot','slope','donut','waterfall','funnel'):
        labels,ss=_series(d); vals=[num(v) for s in ss for v in s['values']]
        if k not in ('grouped','stacked','stacked100','line','area','slope') and len(ss)!=1:raise ValueError(f'{k} 只接受一条系列')
        n=len(labels)
        if n>24:raise ValueError('超过 24 类请拆图或使用表格')
        if k=='slope' and n!=2:raise ValueError('slope 只接受两个时间点')
        if k in ('stacked','stacked100','donut','funnel') and min(vals)<0:raise ValueError(f'{k} 不接受负数')
        if k=='area' and min(vals)<0:raise ValueError('area 仅用于非负总量；含负值请用 line')
        if k=='donut' and (not 2<=n<=6 or sum(vals)<=0):raise ValueError('donut 需要 2–6 个部分且总和 > 0')
        if k=='funnel' and (any(vals[i]<vals[i+1] for i in range(n-1)) or vals[0]<=0):raise ValueError('漏斗必须是连续阶段的非递增人数；普通比较请用条形图')
        horizontal=k in ('hbar','funnel')
        bottom=max([len(wrap(str(x),max(3,(w-180)/n/16))) for x in labels])*23+22 if not horizontal else 42
        h=max(h,80+bottom+170)
        if horizontal:h=max(h,n*53+70)
        c=Canvas(w,h,p,d.get('title',k)); left=155 if horizontal else 76; right=w-65; top=60+30*math.ceil(len(ss)/3); bot=h-bottom
        if horizontal:bot=h-42
        if k=='donut':
            total=sum(vals); angle=-math.pi/2; cx,cy,r=w*.28,h*.52,min(w*.22,h*.35)
            for i,(lab,v) in enumerate(zip(labels,vals)):
                end=angle+v/total*math.tau
                if v>0:
                    # Split complete circles into two arcs for valid SVG geometry.
                    mid=(angle+end)/2
                    a=(cx+r*math.cos(angle),cy+r*math.sin(angle)); b=(cx+r*math.cos(mid),cy+r*math.sin(mid)); z=(cx+r*math.cos(end),cy+r*math.sin(end))
                    c.path(f'M {a[0]} {a[1]} A {r} {r} 0 0 1 {b[0]} {b[1]} A {r} {r} 0 0 1 {z[0]} {z[1]}',colors[i],width=r*.4)
                yy=75+i*48;c.rect(w*.56,yy-14,14,14,colors[i]);c.text(w*.59,yy,f'{lab}  {fmt(v)}{unit}  ({v/total:.1%})',width=w*.39)
                angle=end
            c.text(cx,cy-3,fmt(total),30,anchor='middle',weight=700);c.text(cx,cy+28,unit or '合计',anchor='middle')
            return c.finish()
        if k in ('stacked','stacked100'):
            totals=[sum(num(s['values'][i]) for s in ss) for i in range(n)]
            if k=='stacked100' and any(t<=0 for t in totals):raise ValueError('百分比堆叠每类的总数必须 > 0')
            lo,hi=0,100 if k=='stacked100' else max(totals,default=1)
            if hi==0:hi=1
        elif k=='waterfall':
            running=[0]
            for v in vals:running.append(running[-1]+v)
            lo,hi=extent(running,True)
        else:lo,hi=extent(vals,zero=k not in ('line','dot','slope'))
        if horizontal:
            x=scale(lo,hi,left,right)
            for t in np.linspace(lo,hi,5):c.line(x(t),top,x(t),bot);c.text(x(t),bot+27,fmt(t),anchor='middle')
            for i,(lab,v) in enumerate(zip(labels,vals)):
                yy=top+(bot-top)*(i+.5)/n;c.text(left-14,yy+5,lab,anchor='end',width=left-24)
                if k=='funnel':
                    bw=(right-left)*v/hi;c.rect((left+right-bw)/2,yy-14,bw,28,colors[i%6],r=2)
                else:c.rect(min(x(0),x(v)),yy-12,abs(x(v)-x(0)),24,colors[i%6],r=2)
                c.text(right+9,yy+5,fmt(v),size=15)
        else:
            y=scale(lo,hi,bot,top); step=(right-left)/n; xc=lambda i:left+step*(i+.5)
            for t in np.linspace(lo,hi,5):c.line(left,y(t),right,y(t));c.text(left-12,y(t)+5,fmt(t),anchor='end')
            for i,lab in enumerate(labels):c.text(xc(i),bot+28,lab,anchor='middle',width=step-8)
            if k in ('line','area','slope'):
                for j,s in enumerate(ss):
                    path=' '.join(f'{"M" if i==0 else "L"}{xc(i):.2f} {y(v):.2f}' for i,v in enumerate(s['values']))
                    if k=='area':c.path(path+f' L{xc(n-1)} {y(0)} L{xc(0)} {y(0)} Z',fill=mix(colors[j],p['paper'],.83))
                    c.path(path,colors[j],width=3)
                    for i,v in enumerate(s['values']):c.circle(xc(i),y(v),4.5,colors[j])
            elif k in ('stacked','stacked100'):
                for i in range(n):
                    acc=0
                    for j,s in enumerate(ss):
                        v=num(s['values'][i]);v=v/totals[i]*100 if k=='stacked100' else v
                        c.rect(xc(i)-step*.28,y(acc+v),step*.56,y(acc)-y(acc+v),colors[j]);acc+=v
                    c.text(xc(i),y(acc)-10,f'{fmt(totals[i])}',15,anchor='middle')
            elif k=='waterfall':
                acc=0
                for i,v in enumerate(vals):
                    new=acc+v;c.rect(xc(i)-step*.28,min(y(acc),y(new)),step*.56,abs(y(new)-y(acc)),p['accent'] if v>=0 else p['accent2']);c.text(xc(i),min(y(acc),y(new))-10,fmt(v),15,anchor='middle')
                    if i<n-1:c.line(xc(i)+step*.28,y(new),xc(i+1)-step*.28,y(new),p['mut'],dash='4 3')
                    acc=new
            else:
                for j,s in enumerate(ss):
                    for i,v in enumerate(s['values']):
                        bw=step*.65/len(ss);xx=xc(i)-step*.325+j*bw
                        if k=='dot':c.circle(xc(i),y(v),7,colors[i%6])
                        else:c.rect(xx,min(y(0),y(v)),bw*.85,abs(y(v)-y(0)),colors[j] if k=='grouped' else colors[i%6],r=2)
                        c.text(xx+bw*.425 if k!='dot' else xc(i),y(v)-10 if v>=0 else y(v)+23,fmt(v),15,anchor='middle')
        c.text(left,27,unit,fill=p['mut'])
        for j,s in enumerate(ss):
            xx=left+(j%3)*((right-left)/3);yy=51+(j//3)*30;c.rect(xx,yy-12,12,12,colors[j]);c.text(xx+20,yy,s['name'],size=15,width=(right-left)/3-26)
        return c.finish()
    if k=='gantt':
        tasks=d['tasks']
        if not tasks:raise ValueError('gantt.tasks 不能为空')
        parse=lambda s:dt.date.fromisoformat(s).toordinal()
        starts=[parse(t['start']) for t in tasks];ends=[parse(t['end']) for t in tasks]
        if any(b<a for a,b in zip(starts,ends)):raise ValueError('任务结束不得早于开始')
        h=max(h,len(tasks)*58+100);c=Canvas(w,h,p,'任务与工期');a,b=min(starts),max(ends);x=scale(a,b,180,w-55)
        for t in np.linspace(a,b,5):c.line(x(t),70,x(t),h-48);c.text(x(t),h-17,dt.date.fromordinal(round(t)).isoformat()[5:],anchor='middle')
        for i,t in enumerate(tasks):
            yy=90+i*58;c.text(160,yy+5,t['name'],anchor='end',width=150)
            if t.get('milestone'):c.path(f'M{x(starts[i])} {yy-10} l10 10 l-10 10 l-10 -10 Z',fill=p['accent'])
            else:c.rect(x(starts[i]),yy-12,max(3,x(ends[i])-x(starts[i])),24,colors[i%6],r=3)
        c.text(180,30,f'{dt.date.fromordinal(a).isoformat()} — {dt.date.fromordinal(b).isoformat()}',fill=p['mut']);return c.finish()
    if k=='heatmap':
        rows,cols,vs=d['rows'],d['columns'],d['values']
        if len(vs)!=len(rows) or not rows or not cols or any(len(r)!=len(cols) for r in vs):raise ValueError('heatmap 行列尺寸不匹配')
        lo,hi=extent([v for r in vs for v in r]);h=max(h,130+len(rows)*54);c=Canvas(w,h,p,'矩阵热图');cw=(w-180)/len(cols)
        for j,s in enumerate(cols):c.text(160+cw*(j+.5),37,s,anchor='middle',width=cw-8)
        for i,row in enumerate(vs):
            yy=75+i*54;c.text(143,yy+28,rows[i],anchor='end',width=130)
            for j,v in enumerate(row):
                col=mix(p['tint'],p['accent'],(num(v)-lo)/(hi-lo));c.rect(160+j*cw,yy,cw-3,50,col);c.text(160+cw*(j+.5),yy+30,fmt(v),fill=on_color(col),anchor='middle')
        c.text(160,h-12,f'{unit} · 浅色 {fmt(lo)} → 深色 {fmt(hi)}',fill=p['mut']);return c.finish()
    if k=='range':
        items=d['items'];vs=[]
        if not d.get('interval_label'):raise ValueError('range 必须说明区间口径 interval_label')
        for z in items:
            a,v,b=map(num,(z['low'],z['value'],z['high']))
            if not a<=v<=b:raise ValueError('range 需要 low ≤ value ≤ high')
            vs.extend([a,b])
        lo,hi=extent(vs);h=max(h,100+len(items)*58);c=Canvas(w,h,p,'点与区间');x=scale(lo,hi,180,w-70)
        for i,z in enumerate(items):
            yy=75+i*58;c.text(160,yy+5,z['label'],anchor='end',width=150);c.line(x(z['low']),yy,x(z['high']),yy,p['accent'],5);c.circle(x(z['value']),yy,7,p['ink']);c.text(x(z['value']),yy-14,fmt(z['value']),15,anchor='middle')
        for v in np.linspace(lo,hi,5):c.text(x(v),h-45,fmt(v),anchor='middle')
        c.text(180,h-12,d['interval_label']+' · '+unit,fill=p['mut']);return c.finish()
    if k=='histogram':
        vals=[num(v) for v in d['samples']]
        if not vals:raise ValueError('histogram 需要原始样本')
        counts,bins=np.histogram(vals,bins=d.get('bins','auto'))
        dd={'kind':'bar','unit':'频数','labels':[f'{a:g}–{b:g}' for a,b in zip(bins,bins[1:])],'series':[{'name':d.get('unit','测量值')+'；左闭右开，末组包含右端点','values':counts.tolist()}]}
        return make(dd,p,w,h)
    if k=='box':
        groups=d['groups'];vs=[num(v) for g in groups for v in g['values']];lo,hi=extent(vs)
        c=Canvas(w,h,p,'箱线图');y=scale(lo,hi,h-65,55);step=(w-140)/len(groups)
        for t in np.linspace(lo,hi,5):c.line(70,y(t),w-40,y(t));c.text(58,y(t)+5,fmt(t),anchor='end')
        for i,g in enumerate(groups):
            if not g['values']:raise ValueError('箱线图每组至少一个值')
            q1,med,q3=np.quantile(g['values'],[.25,.5,.75]);iqr=q3-q1;inside=[v for v in g['values'] if q1-1.5*iqr<=v<=q3+1.5*iqr];a,b=min(inside),max(inside);xx=70+step*(i+.5)
            c.line(xx,y(a),xx,y(b),p['ink']);c.rect(xx-step*.2,y(q3),step*.4,y(q1)-y(q3),mix(colors[i%6],p['paper'],.65),colors[i%6]);c.line(xx-step*.2,y(med),xx+step*.2,y(med),p['ink'],3)
            for v in g['values']:
                if v<a or v>b:c.circle(xx,y(v),4,p['paper'],p['ink'])
            c.text(xx,h-34,g['name'],anchor='middle',width=step-8)
        c.text(70,25,unit+' · 线为中位数，箱为 Q1–Q3，须为 1.5 IQR 范围',size=15,fill=p['mut']);return c.finish()
    if k=='scatter':
        pts=d['points'];xs=[num(t['x']) for t in pts];ys=[num(t['y']) for t in pts];xl,xh=extent(xs);yl,yh=extent(ys);c=Canvas(w,h,p,'散点图');x=scale(xl,xh,90,w-65);y=scale(yl,yh,h-75,50)
        for v in np.linspace(yl,yh,5):c.line(90,y(v),w-65,y(v));c.text(73,y(v)+5,fmt(v),anchor='end')
        for v in np.linspace(xl,xh,5):c.text(x(v),h-45,fmt(v),anchor='middle')
        for t in pts:
            radius=5
            if 'size' in t:
                if num(t['size'])<0:raise ValueError('气泡面积不能为负')
                radius=math.sqrt(num(t['size']))*d.get('size_scale',2)
            c.circle(x(t['x']),y(t['y']),radius,p['accent'])
        c.text(90,27,d.get('y_unit','y'),fill=p['mut']);c.text(w-65,h-10,d.get('x_unit','x'),fill=p['mut'],anchor='end');return c.finish()
    raise ValueError(k)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('request');ap.add_argument('output');ap.add_argument('--palette',default='midnight');a=ap.parse_args()
    Path(a.output).write_text(make(json.loads(Path(a.request).read_text()),resolve_palette(a.palette)),encoding='utf-8')
