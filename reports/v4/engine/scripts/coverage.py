"""Content conservation: coverage references plus exact rendered text, never references alone."""
import re

def norm(s):return re.sub(r'\s+','',str(s))

def walk(obj):
    if isinstance(obj,dict):
        yield obj
        for v in obj.values():yield from walk(v)
    elif isinstance(obj,list):
        for v in obj:yield from walk(v)

def check(spec,inventory,pdf_text=None):
    units={u['id']:u for u in inventory.get('units',[])};seen={};refs=set();errors=[];warnings=[];fragments={}
    for b in walk(spec.get('pages',[])):
        if b.get('type')=='source':
            for sid in b.get('ids',[]):
                if sid not in units:errors.append(f'未知原文单元 {sid}');continue
                u=units[sid];text=b.get('fragments',{}).get(sid,u.get('text',''))
                seen[sid]=seen.get(sid,0)+1;fragments.setdefault(sid,[]).append(text)
        for sid in b.get('source_ids',[]):
            if sid not in units:errors.append(f'未知 source_ids {sid}');continue
            refs.add(sid)
            u=units[sid]
            if u['kind']=='text':
                # A mapped rewritten block requires an explicit, reviewable editorial decision.
                if not spec.get('document',{}).get('allow_rewrite') or not b.get('rewrite_note'):
                    errors.append(f'{sid} 用 source_ids 引用但未以 source 原文保留；重写须 allow_rewrite=true 且逐块写 rewrite_note')
            elif not b.get('src'):
                errors.append(f'{sid} 是图像：须使用 source，或在带 source_ids 的图组件上提供 src')
    omitted={x['id']:x for x in spec.get('omissions',[])}
    for sid in omitted:
        if sid not in units:errors.append(f'omissions 中有未知单元 {sid}')
    for sid,u in units.items():
        if not u.get('required',True):
            warnings.append(f'{sid} 被设为非必保留项；该标记不豁免覆盖检查，省略仍须用户授权')
        if sid in seen:
            if u['kind']=='text' and norm(''.join(fragments[sid]))!=norm(u['text']):errors.append(f'{sid} 的原文片段不完整或重复')
        elif sid in refs:warnings.append(f'{sid} 已重写：需人工逐项核对语义与限定条件')
        elif sid in omitted:
            if not omitted[sid].get('reason') or not omitted[sid].get('user_authorized'):errors.append(f'{sid} 的省略缺少原因或用户授权')
            else:warnings.append(f'{sid} 经用户授权省略：{omitted[sid]["reason"]}')
        else:errors.append(f'未保留原文单元 {sid}（{u.get("source","")} p{u.get("page","-")}）')
    if pdf_text is not None:
        pt=norm(pdf_text)
        for sid,parts in fragments.items():
            if units[sid]['kind']!='text':continue
            for part in parts:
                if norm(part) not in pt:errors.append(f'最终 PDF 中未检出原文片段 {sid}，检查字体、裁切和阅读顺序')
    return {'total':len(units),'verbatim':len(seen),'rewritten':len(refs-set(seen)),'omitted':len(omitted),'errors':errors,'warnings':warnings,'semantic_review_required':bool(refs-set(seen))}
