"""Add only missing game characters to the existing V3 font families.

The original three WOFF2 files remain byte-for-byte unchanged. Full Noto font
sources can be obtained from the fixed URLs in site/fonts/sources.json.
"""
import argparse
import hashlib
import json
from pathlib import Path
from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[2]
FACES = [
    ('sans-regular', 'BeforeStep Sans', 400, 'NotoSansCJKsc-Regular.otf'),
    ('sans-bold', 'BeforeStep Sans', 700, 'NotoSansCJKsc-Bold.otf'),
    ('serif-bold', 'BeforeStep Serif', 700, 'NotoSerifCJKsc-Bold.otf'),
]
TEXT_FILES = ['play.html', 'index.html', 'mission.js', 'mission-story.js', 'mission-worker.js', 'mission-observation.js', 'mission-run.js', 'mission-gameplay.js', 'mission-insight.js', 'mission-scene.js']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir', type=Path, required=True)
    parser.add_argument('--existing-dir', type=Path, default=ROOT / 'site/fonts')
    args = parser.parse_args()
    output = ROOT / 'site/fonts'
    output.mkdir(parents=True, exist_ok=True)
    text = '\n'.join((ROOT / 'site' / name).read_text() for name in TEXT_FILES)
    required = {ord(c) for c in text if '\u3400' <= c <= '\u9fff'}
    rows, css = [], ['/* Supplement to the unchanged V3 Noto font families. */']
    for face, family, weight, source_name in FACES:
        original = args.existing_dir / f'beforestep-{face}.woff2'
        source = args.source_dir / source_name
        with TTFont(original) as font:
            missing = sorted(required - set(font.getBestCmap()))
        row = {'face': face, 'original': original.name, 'original_sha256': sha(original),
               'source': source.name, 'source_sha256': sha(source),
               'required_cjk_count': len(required), 'added_codepoints': missing}
        if missing:
            with TTFont(source) as font:
                absent = set(missing) - set(font.getBestCmap())
                if absent:
                    raise ValueError(f'{source_name}: missing source characters {absent}')
                options = subset.Options()
                options.recalc_timestamp = False
                options.flavor = 'woff2'
                cutter = subset.Subsetter(options=options)
                cutter.populate(unicodes=missing)
                cutter.subset(font)
                font.flavor = 'woff2'
                font.recalcTimestamp = False
                target = output / f'beforestep-gameplay-{face}.woff2'
                font.save(target)
            row.update(file=target.name, sha256=sha(target), bytes=target.stat().st_size)
            ranges = ','.join(f'U+{cp:X}' for cp in missing)
            css.append(f'@font-face{{font-family:"{family}";src:url("{target.name}?v={row["sha256"][:12]}") format("woff2");font-style:normal;font-weight:{weight};font-display:swap;unicode-range:{ranges}}}')
        rows.append(row)
    (output / 'gameplay.css').write_text('\n'.join(css) + '\n')
    result = {'schema': 'beforestep-gameplay-fonts/v1', 'license': 'OFL.txt',
              'fixed_source_urls': 'sources.json', 'text_sources': TEXT_FILES,
              'original_fonts_unchanged': True, 'faces': rows}
    (output / 'gameplay-provenance.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'passed': True, 'faces': [{'face': r['face'], 'added': len(r['added_codepoints']), 'bytes': r.get('bytes', 0)} for r in rows]}))


if __name__ == '__main__':
    main()
