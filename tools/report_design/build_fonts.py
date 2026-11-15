"""Build the report's Noto CJK webfont subsets for the current interface.

Install fonttools and brotli. Optional --source-dir reuses downloaded OTF files.
The matching original fonts are distributed under the included SIL OFL 1.1.
"""
from __future__ import annotations
import argparse
import hashlib
import html
import json
import logging
from pathlib import Path
import tempfile
from urllib.request import urlopen
from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[2]
BASE = "https://raw.githubusercontent.com/notofonts/noto-cjk/f8d157532fbfaeda587e826d4cd5b21a49186f7c/"
SOURCES = [
    ("Serif/OTF/SimplifiedChinese/NotoSerifCJKsc-Bold.otf", "beforestep-serif-bold.woff2", "BeforeStep Serif", "Bold"),
    ("Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Regular.otf", "beforestep-sans-regular.woff2", "BeforeStep Sans", "Regular"),
    ("Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Bold.otf", "beforestep-sans-bold.woff2", "BeforeStep Sans", "Bold"),
]

def build(source_dir: Path) -> None:
    logging.getLogger("fontTools.subset").setLevel(logging.ERROR)
    out = ROOT / "site/fonts"
    out.mkdir(parents=True, exist_ok=True)
    text = ""
    for file in sorted((ROOT / "site").rglob("*")):
        if file.suffix in {".html", ".js", ".json"} and "vendor" not in file.parts:
            text += html.unescape(file.read_text(encoding="utf-8", errors="ignore"))
    codes = {ord(c) for c in text}
    for start, end in [(0x20, 0x180), (0x370, 0x400), (0x2190, 0x2200), (0x2460, 0x2500), (0x2700, 0x2800), (0x3000, 0x3040)]:
        codes.update(range(start, end))
    manifests = []
    for path, name, family, style in SOURCES:
        original = source_dir / Path(path).name
        if not original.exists():
            with urlopen(BASE + path, timeout=60) as response:
                original.write_bytes(response.read())
        font = TTFont(original, recalcTimestamp=False)
        available = set(font.getBestCmap())
        options = subset.Options()
        options.flavor = "woff2"
        options.layout_features = ["*"]
        options.name_IDs = ["*"]
        sub = subset.Subsetter(options=options)
        sub.populate(unicodes=codes & available)
        sub.subset(font)
        for name_id, value in [(1, family), (2, style), (3, family + " " + style), (4, family + " " + style), (6, family.replace(" ", "") + "-" + style), (16, family), (17, style)]:
            font["name"].setName(value, name_id, 3, 1, 0x409)
        font.flavor = "woff2"
        destination = out / name
        font.save(destination)
        manifests.append({"file": name, "family": family, "style": style,
                          "source_url": BASE + path,
                          "source_sha256": hashlib.sha256(original.read_bytes()).hexdigest(),
                          "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
                          "bytes": destination.stat().st_size,
                          "covered_codepoints": len(codes & available)})
    license_file = source_dir / "Sans-OFL.txt"
    if not license_file.exists():
        with urlopen(BASE + "Sans/LICENSE", timeout=30) as response:
            license_file.write_bytes(response.read())
    (out / "OFL.txt").write_bytes(license_file.read_bytes())
    (out / "sources.json").write_text(json.dumps({"license": "SIL Open Font License 1.1", "fonts": manifests}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifests, ensure_ascii=False))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path)
    args = parser.parse_args()
    if args.source_dir:
        args.source_dir.mkdir(parents=True, exist_ok=True)
        build(args.source_dir)
    else:
        with tempfile.TemporaryDirectory(prefix="beforestep-report-fonts-") as folder:
            build(Path(folder))
