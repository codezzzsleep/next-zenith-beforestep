"""Check the final report, including visible CJK glyphs and rebuild equivalence."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import numpy as np
import pymupdf

ROOT = Path(__file__).resolve().parents[1]

def verify(pdf, reference=None):
    doc = pymupdf.open(pdf)
    if len(doc) != 14:
        raise ValueError(f'Expected reviewed 14-page layout, got {len(doc)}')
    text = '\n'.join(p.get_text() for p in doc)
    norm = re.sub(r'\s+', '', text)
    spec = json.loads((ROOT / 'spec.json').read_text(encoding='utf-8'))
    for fact in spec['facts']:
        if re.sub(r'\s+', '', fact['display']) not in norm:
            raise ValueError(f'Missing fact display: {fact["id"]}')
    for phrase in ['一张照片', '局部试验', '自动制动', '小气泡中旋转', '所选GLB参与碰撞计算',
                   '看完模型只释放手控', '5分33秒', '不是实机']:
        if phrase not in norm:
            raise ValueError(f'Missing report statement: {phrase}')
    blank = []
    outside = []
    count = 0
    scale = 120 / 72
    for n, page in enumerate(doc, 1):
        pix = page.get_pixmap(dpi=120, alpha=False)
        rgb = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        for block in page.get_text('rawdict')['blocks']:
            if block['type'] != 0:
                continue
            for line in block['lines']:
                for span in line['spans']:
                    for char in span['chars']:
                        x0, y0, x1, y1 = char['bbox']
                        if x0 < -1 or y0 < -1 or x1 > page.rect.width+1 or y1 > page.rect.height+1:
                            outside.append({'page':n, 'text':char['c']})
                        if not re.search(r'[\u4e00-\u9fff]', char['c']):
                            continue
                        count += 1
                        crop = rgb[max(0,int(y0*scale)):min(pix.height,int(y1*scale)+1),
                                   max(0,int(x0*scale)):min(pix.width,int(x1*scale)+1)]
                        if not crop.size or np.ptp(crop.reshape(-1,pix.n), axis=0).max() < 24:
                            blank.append({'page':n, 'text':char['c'], 'bbox':list(char['bbox'])})
    if blank or outside:
        raise ValueError(json.dumps({'blank_CJK':blank[:15], 'outside':outside[:15]}, ensure_ascii=False))
    result = {'pages':len(doc), 'bytes':pdf.stat().st_size,
              'sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(), 'CJK_glyph_regions_checked':count,
              'blank_CJK_regions':0, 'text_outside_pages':0, 'fact_displays_checked':len(spec['facts']),
              'replacement_characters':text.count('\ufffd'),
              'new_game_features_and_scope_present':True,
              'fonts':sorted({font[3] for page in doc for font in page.get_fonts()})}
    if result['replacement_characters']:
        raise ValueError('Replacement characters in PDF text')
    if reference:
        original = pymupdf.open(reference)
        if len(doc) != len(original) or any(a.get_text()!=b.get_text() for a,b in zip(doc, original)):
            raise ValueError('Independent rebuild differs in text or page count')
        for a,b in zip(doc, original):
            if a.get_pixmap(dpi=60).samples != b.get_pixmap(dpi=60).samples:
                raise ValueError('Independent rebuild differs in rendered pages')
        result['independent_rebuild_text_and_60dpi_pixels_equal'] = True
    return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pdf', type=Path)
    parser.add_argument('--reference', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = verify(args.pdf, args.reference)
    data = json.dumps(result, ensure_ascii=False, indent=2)+'\n'
    if args.output:
        args.output.write_text(data, encoding='utf-8')
    print(data)
