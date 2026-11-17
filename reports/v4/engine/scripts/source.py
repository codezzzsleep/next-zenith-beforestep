"""Extract a PDF into a source ledger, preserving original text and rendered page evidence.
Extracted blocks are a starting inventory, not semantic proof of OCR or table fidelity.
"""
import argparse,json,hashlib
from pathlib import Path
import fitz

def extract(pdf,out):
    src=Path(pdf).resolve();dest=Path(out).resolve();dest.mkdir(parents=True,exist_ok=True);assets=dest/'source-assets';assets.mkdir(exist_ok=True)
    units=[];warnings=[];doc=fitz.open(src)
    for pn,page in enumerate(doc,1):
        count=0
        for bn,b in enumerate(page.get_text('blocks',sort=True),1):
            if b[6]!=0 or not b[4].strip():continue
            # Preserve source line breaks; reflowing is a design decision made later.
            units.append({'id':f'p{pn:03d}-t{bn:03d}','kind':'text','text':b[4].strip(),'source':src.name,'page':pn,'bbox':list(b[:4]),'required':True});count+=1
        if not count:warnings.append(f'第 {pn} 页无可提取文字：需人工核对或 OCR，不可视为内容为空。')
        # Preserve a rendered full-page reference even for vectors, charts, masks and text baked into images.
        # Do not blindly insert this reference into redesigned pages: inventory real figures separately.
        page.get_pixmap(matrix=fitz.Matrix(1.5,1.5),alpha=False).save(assets/f'page-{pn:03d}.png')
        # PDF resource dictionaries may be shared across every page. Only displayed
        # occurrences belong in this page's ledger; get_images() would duplicate them.
        for j,img in enumerate(page.get_image_info(xrefs=True),1):
            xref=img.get('xref',0)
            try:
                bbox=fitz.Rect(img['bbox']) & page.rect
                if bbox.is_empty:continue
                asset=assets/f'p{pn:03d}-image{j:03d}.png'
                # The displayed crop retains transparency masks, overlays and labels.
                page.get_pixmap(matrix=fitz.Matrix(2,2),clip=bbox,alpha=False).save(asset)
                units.append({'id':f'p{pn:03d}-i{j:03d}','kind':'image','asset':str(asset.relative_to(dest)),'text':f'原始图像 · {src.name} 第 {pn} 页，图 {j}','source':src.name,'page':pn,'bbox':list(bbox),'xref':xref,'required':True})
            except Exception as e:warnings.append(f'第 {pn} 页图像 {j} 无法提取：{type(e).__name__}，请从原页参考图核对。')
        if page.get_drawings():warnings.append(f'第 {pn} 页含矢量对象：逐页核对图表、流程、表格与图例；尚未自动建立独立图像单元。')
    result={'version':1,'source':{'filename':src.name,'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'pages':len(doc)},'inventory_reviewed':False,'warnings':warnings,'units':units,'review_note':'逐页与 source-assets/page-*.png 核对阅读顺序、矢量图、图片蒙版、表格与脚注；补齐未提取的图，再设置 inventory_reviewed=true。不可自动去重或删页眉。'}
    (dest/'inventory.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return result

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('pdf');a.add_argument('directory');v=a.parse_args();r=extract(v.pdf,v.directory);print(json.dumps({'units':len(r['units']),'pages':r['source']['pages'],'warnings':r['warnings'],'review_required':True},ensure_ascii=False))
