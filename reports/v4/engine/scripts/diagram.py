"""Deterministic topology: flow, tree, architecture, swimlane, cycle.
Arrows mean declared relationships. Never infer causal edges from card order.
"""
import argparse,json,math
from pathlib import Path
from core import resolve_palette,wrap,esc,mix
from svg import Canvas

KINDS=('flow','tree','architecture','swimlane','cycle')

def sample(kind):
    d={'kind':kind,'nodes':[{'id':'a','label':'输入材料'},{'id':'b','label':'识别信息关系'},{'id':'c','label':'选择表达形式'},{'id':'d','label':'核对与交付'}], 'edges':[{'from':'a','to':'b'},{'from':'b','to':'c'},{'from':'c','to':'d'}]}
    if kind=='flow':d['nodes'][1]['shape']='decision';d['edges'][1]['label']='可视化有帮助'
    if kind=='tree':d['edges']=[{'from':'a','to':x} for x in ['b','c','d']]
    if kind=='swimlane':
        d['lanes']=['资料','设计','验证']
        for i,n in enumerate(d['nodes']):n['lane']=d['lanes'][min(i,2)]
    if kind=='cycle':d['edges'].append({'from':'d','to':'a'})
    return d

def make(d,pal=None,width=900):
    p=pal or resolve_palette('midnight');k=d['kind'];nodes=d['nodes'];edges=d.get('edges',[])
    if k not in KINDS:raise ValueError(f'未知结构图 {k}')
    if not 1<=len(nodes)<=16:raise ValueError('单图只放 1–16 节点；更多节点先拆分主流程与子流程')
    ids=[n['id'] for n in nodes]
    if len(set(ids))!=len(ids):raise ValueError('节点 id 不得重复')
    incoming={i:[] for i in ids};outgoing={i:[] for i in ids}
    for e in edges:
        if e['from'] not in ids or e['to'] not in ids:raise ValueError('连线端点必须存在')
        incoming[e['to']].append(e['from']);outgoing[e['from']].append(e['to'])
    bw,bh=220,82
    maxlines=max(len(wrap(n['label'],11)) for n in nodes);bh=max(bh,maxlines*24+34)
    pos={}
    if k=='cycle':
        if not 3<=len(nodes)<=8:raise ValueError('循环图使用 3–8 个节点')
        actual={(e['from'],e['to']) for e in edges};expected={(ids[i],ids[(i+1)%len(ids)]) for i in range(len(ids))}
        if actual!=expected:raise ValueError('cycle 的边必须构成按 nodes 顺序的一个有向闭环')
        h=760;cx,cy=width/2,h/2;rx,ry=width*.33,h*.34;bw=190
        for i,n in enumerate(nodes):
            a=-math.pi/2+math.tau*i/len(nodes);pos[n['id']]=(cx+rx*math.cos(a)-bw/2,cy+ry*math.sin(a)-bh/2)
    else:
        levels={};pending=set(ids)
        while pending:
            ready=[i for i in ids if i in pending and all(j in levels for j in incoming[i])]
            if not ready:raise ValueError('存在回路：将主干与回路拆图，或用 cycle 明确绘制闭环')
            for i in ready:levels[i]=max([levels[j]+1 for j in incoming[i]] or [0]);pending.remove(i)
        if k=='tree' and any(len(v)>1 for v in incoming.values()):raise ValueError('tree 每个子节点只能有一个父节点')
        groups={}
        for n in nodes:groups.setdefault(levels[n['id']],[]).append(n)
        if k=='swimlane':
            lanes=d.get('lanes',[])
            if not 1<=len(lanes)<=4 or len(set(lanes))!=len(lanes):raise ValueError('泳道图需要 1–4 个不重名的 lanes')
            if any(n.get('lane') not in lanes for n in nodes):raise ValueError('每个节点必须属于已定义的泳道')
            bw=(width-90)/len(lanes)-28
            # Keep one node per row, preserving all declared edges and lanes.
            order=sorted(nodes,key=lambda n:(levels[n['id']],ids.index(n['id'])))
            h=95+len(order)*(bh+55)
            for row,n in enumerate(order):pos[n['id']]=(72+lanes.index(n['lane'])*((width-90)/len(lanes)),70+row*(bh+55))
        else:
            if any(len(g)>4 for g in groups.values()):raise ValueError('同层超过 4 节点：请分组为子图')
            bw=min(240,(width-80)/max(len(g) for g in groups.values())-22)
            bh=max(82,max(len(wrap(n['label'],(bw-34)/17)) for n in nodes)*24+34)
            h=75+(max(levels.values())+1)*(bh+64)
            for lv,g in groups.items():
                total=len(g)*bw+(len(g)-1)*22
                for j,n in enumerate(g):pos[n['id']]=((width-total)/2+j*(bw+22),35+lv*(bh+64))
    c=Canvas(width,h,p,d.get('title',k))
    if k=='swimlane':
        for j,l in enumerate(d['lanes']):
            xx=60+j*(width-90)/len(d['lanes']);c.rect(xx,5,(width-90)/len(d['lanes'])-6,h-12,p['tint']);c.text(xx+12,35,l,weight=700)
    marker='arrow'+str(abs(sum(ord(ch) for ch in json.dumps(d,ensure_ascii=False))))
    c.parts.append(f'<defs><marker id="{marker}" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto"><path d="M0 0 L9 4.5 L0 9 Z" fill="{p["mut"]}"/></marker></defs>')
    for e in edges:
        ax,ay=pos[e['from']];bx,by=pos[e['to']]
        if k=='cycle':
            dx,dy=(bx-ax),(by-ay);dist=math.hypot(dx,dy);sx,sy=ax+bw/2+dx/dist*min(bw,bh)/2,ay+bh/2+dy/dist*min(bw,bh)/2;tx,ty=bx+bw/2-dx/dist*min(bw,bh)/2,by+bh/2-dy/dist*min(bw,bh)/2
            path=f'M{sx} {sy} L{tx} {ty}'
        else:
            sx,sy=ax+bw/2,ay+bh;tx,ty=bx+bw/2,by;mid=(sy+ty)/2
            path=f'M{sx} {sy} L{sx} {mid} L{tx} {mid} L{tx} {ty-5}'
        c.path(path,p['mut'],width=2,extra=f'marker-end="url(#{marker})"')
        if e.get('label'):c.text((sx+tx)/2+8,(sy+ty)/2-8,e['label'],14,fill=p['ink'],width=180)
    for n in nodes:
        x,y=pos[n['id']];key=n.get('key',False);col=p['dark'] if key else p['paper'];fg=p['on_dark'] if key else p['ink'];shape=n.get('shape','box')
        if shape=='decision':c.path(f'M{x+bw/2} {y-12} L{x+bw+12} {y+bh/2} L{x+bw/2} {y+bh+12} L{x-12} {y+bh/2} Z',p['accent'],p['accent_soft'],2);fg=p['ink']
        else:c.rect(x,y,bw,bh,col,p['accent'] if key else p['line2'],5)
        lines=wrap(n['label'],(bw-32)/17);c.text(x+bw/2,y+bh/2-(len(lines)-1)*12+6,'\n'.join(lines),17,fill=fg,anchor='middle',weight=700)
    return c.finish()

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('request');ap.add_argument('output');ap.add_argument('--palette',default='midnight');a=ap.parse_args();Path(a.output).write_text(make(json.loads(Path(a.request).read_text()),resolve_palette(a.palette)),encoding='utf-8')
