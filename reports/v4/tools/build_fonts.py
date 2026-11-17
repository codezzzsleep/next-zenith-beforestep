"""Regenerate the report subsets from the pinned upstream Noto OTF files.

Pass --source-dir with the three originals listed in fonts/sources.json.
The build itself uses the bundled subsets and does not require this step.
"""
import argparse
import hashlib
import json
import logging
from pathlib import Path
from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://raw.githubusercontent.com/notofonts/noto-cjk/f8d157532fbfaeda587e826d4cd5b21a49186f7c/'
SOURCES = [
    ('Serif/OTF/SimplifiedChinese/NotoSerifCJKsc-Bold.otf', 'BeforeStepReportSerif-Bold.otf', 'BeforeStep Report Serif', 'Bold'),
    ('Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Regular.otf', 'BeforeStepReportSans-Regular.otf', 'BeforeStep Report Sans', 'Regular'),
    ('Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Bold.otf', 'BeforeStepReportSans-Bold.otf', 'BeforeStep Report Sans', 'Bold'),
]

def build(source_dir):
    logging.getLogger('fontTools.subset').setLevel(logging.ERROR)
    out = ROOT / 'fonts'
    out.mkdir(exist_ok=True)
    text = (ROOT / 'spec.json').read_text(encoding='utf-8')
    text += ''.join(p.read_text(encoding='utf-8') for p in (ROOT / 'assets').glob('*.svg'))
    codes = {ord(c) for c in text}
    for start, end in [(0x20, 0x180), (0x2190, 0x2200), (0x2460, 0x2500), (0x3000, 0x3040)]:
        codes.update(range(start, end))
    entries = []
    for path, name, family, style in SOURCES:
        original = source_dir / Path(path).name
        font = TTFont(original, recalcTimestamp=False)
        available = set(font.getBestCmap())
        opts = subset.Options()
        opts.retain_gids = True
        opts.name_IDs = ['*']
        opts.layout_features = ['*']
        sub = subset.Subsetter(options=opts)
        sub.populate(unicodes=codes & available)
        sub.subset(font)
        for nid, value in [(1, family), (2, style), (3, family+' '+style), (4, family+' '+style), (6, family.replace(' ', '')+'-'+style), (16, family), (17, style)]:
            font['name'].setName(value, nid, 3, 1, 0x409)
        dest = out / name
        font.save(dest)
        entries.append({'file':name, 'family':family, 'style':style, 'source_url':BASE+path, 'source_sha256':hashlib.sha256(original.read_bytes()).hexdigest(), 'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(), 'bytes':dest.stat().st_size, 'covered_codepoints':len(codes & available)})
    (out / 'sources.json').write_text(json.dumps({'license':'SIL Open Font License 1.1','fonts':entries}, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(entries, ensure_ascii=False))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir', type=Path, required=True)
    build(parser.parse_args().source_dir)
