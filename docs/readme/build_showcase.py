#!/usr/bin/env python3
"""Build responsive README boards from retained, SHA-checked project images."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

PAPER = "#f6f3ec"
CARD = "#fffdfa"
INK = "#1c304b"
MUTED = "#66717d"
GOLD = "#ad8045"
LINE = "#d9d1c4"
SOURCE_MANIFEST = "docs/readme/sources.json"
EVIDENCE_MANIFEST = "site/media/home-evidence-20261118/sources.json"
GRID_PANEL = "site/media/home-evidence-20261118/02-twelve-world-rehearsals.jpg"
GRID_SHA = "9e38dd6111d9015804e15a1d2bb7387cd7ccf106761a188eba1a46bc052a9667"
# The previous evidence builder fits the complete 1920x1080 frame into this
# rectangle. This removes only its added paper title and footer, not video panes.
GRID_RECT = (176, 127, 1424, 829)
FLOW = [
    ("01 / 观测", "看见的一面", "原 RGB 照片",
     "site/media/real-footage/r1-task-5958685-input.jpg",
     "36c6920301bb5aee1a23970af7b9229a100ee42ffb0aa70f9e84edd61c2aa5cd"),
    ("02 / Lux3D", "可能的背面", "真实 Lux3D 返回",
     "site/media/home-lux3d/model-5958685.jpg",
     "feadecd1eefa082eb473208558224b77f7bd81426282e9cff5ed8e3ffe638461"),
    ("03 / 预演", "在假设里试走", "R1 / 完整 12 世界",
     GRID_PANEL, GRID_SHA),
    ("04 / 行动", "回到原场景", "独立运行检验判断",
     "site/media/home-lux3d/action.jpg",
     "3d544b4353b613f7d8596e35fc417fe14ab51bee02885d6138a925100708f6c3"),
]
VERSIONS = [
    ("V6", "观测约束融合"),
    ("V7", "双视角核对"),
    ("V8", "窄道候选"),
    ("v0.1", "模块化预演"),
    ("v0.2", "完整通行"),
    ("v0.3", "训练控制器"),
]
PAIR = [
    ("真实模型 / Aholo Viewer", "docs/readme/viewer.jpg"),
    ("独立行动 / R1 · Go2W", "docs/readme/robot-action.jpg"),
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path,
                        default=Path(__file__).resolve().parents[2])
    parser.add_argument("--source-root", type=Path,
                        help="Checkout containing the original retained images")
    parser.add_argument("--out", type=Path, default=Path("outputs/readme-showcase"),
                        help="New output directory; an existing directory is refused")
    parser.add_argument("--sans", type=Path, required=True,
                        help="NotoSansCJKsc-Bold.otf or compatible CJK font")
    parser.add_argument("--serif", type=Path, required=True,
                        help="NotoSerifCJKsc-Bold.otf or compatible CJK font")
    args = parser.parse_args()
    repo = args.repo.resolve()
    source = (args.source_root or repo).resolve()
    out = args.out.resolve()
    old_manifest = json.loads((source / SOURCE_MANIFEST).read_text())
    evidence_manifest = json.loads((source / EVIDENCE_MANIFEST).read_text())
    original_files = {item["path"]: item for item in old_manifest["files"]}
    source_checks = {}

    def checked(relative: str, expected: str) -> Path:
        path = source / relative
        actual = sha(path)
        if actual != expected:
            raise ValueError(f"Retained source bytes differ: {relative}")
        source_checks[relative] = {"path": relative, "sha256": actual,
                                   "bytes": path.stat().st_size}
        return path

    for relative, item in original_files.items():
        checked(relative, item["sha256"])
    checked(SOURCE_MANIFEST, sha(source / SOURCE_MANIFEST))
    checked(EVIDENCE_MANIFEST, sha(source / EVIDENCE_MANIFEST))
    for _, _, _, relative, expected in FLOW:
        checked(relative, expected)
    assert evidence_manifest["twelve_worlds"]["layout"] == {
        "columns": 4, "rows": 3, "worlds": 12}
    assert evidence_manifest["twelve_worlds"]["video_time_s"] == 3

    if out.exists():
        raise FileExistsError(f"Choose a new output directory: {out}")
    if not args.sans.is_file() or not args.serif.is_file():
        raise FileNotFoundError("Both CJK font files are required")
    out.mkdir(parents=True)
    sans = lambda size: ImageFont.truetype(str(args.sans), size)
    serif = lambda size: ImageFont.truetype(str(args.serif), size)
    files = []
    text_bounds = []

    def write(draw, xy, content, font, color, max_width):
        bounds = draw.textbbox(xy, content, font=font)
        if bounds[2] - xy[0] > max_width:
            raise ValueError(f"Label overflows its card: {content}")
        draw.text(xy, content, font=font, fill=color)
        text_bounds.append({"text": content, "box": list(bounds)})

    def board(width, height, title, subtitle):
        im = Image.new("RGB", (width, height), PAPER)
        draw = ImageDraw.Draw(im)
        pad = 44 if width == 1600 else 40
        write(draw, (pad, 21), title, serif(50 if width == 1600 else 42),
              INK, width - pad * 2)
        write(draw, (pad, 78), subtitle, sans(24 if width == 1600 else 26),
              MUTED, width - pad * 2)
        draw.line((pad, 115, width - pad, 115), fill=LINE, width=2)
        return im, draw, pad

    def contain(im, image, box):
        x, y, w, h = box
        thumb = ImageOps.contain(image.convert("RGB"), (w, h),
                                 Image.Resampling.LANCZOS)
        im.paste(thumb, (x + (w - thumb.width) // 2,
                        y + (h - thumb.height) // 2))

    def save(im, name, layout):
        path = out / name
        if path.suffix == ".jpg":
            im.save(path, quality=93, optimize=True, subsampling=0)
        else:
            im.save(path, optimize=True)
        files.append({"path": "docs/readme/showcase/" + name,
                      "sha256": sha(path), "bytes": path.stat().st_size,
                      "width": im.width, "height": im.height, "layout": layout})

    def flow(width, columns, name):
        pad = 44 if width == 1600 else 40
        gap = 20
        card_width = (width - pad * 2 - gap * (columns - 1)) // columns
        card_height = 428
        rows = math.ceil(len(FLOW) / columns)
        height = 136 + rows * card_height + (rows - 1) * gap + 32
        im, draw, _ = board(width, height, "把形状带进行动",
                            "原 RGB → 三维假设 → 物理预演 → 独立执行")
        for i, (label, title, caption, relative, _) in enumerate(FLOW):
            x = pad + (i % columns) * (card_width + gap)
            y = 136 + (i // columns) * (card_height + gap)
            draw.rounded_rectangle((x, y, x + card_width, y + card_height),
                                   radius=14, fill=CARD, outline=LINE, width=2)
            write(draw, (x + 20, y + 16), label, sans(28),
                  GOLD, card_width - 40)
            write(draw, (x + 20, y + 58), title, serif(36),
                  INK, card_width - 40)
            with Image.open(source / relative) as picture:
                if relative == GRID_PANEL:
                    assert picture.size == (1600, 900)
                    picture = picture.crop(GRID_RECT)
                    assert picture.size == (1248, 702)
                contain(im, picture, (x + 18, y + 117, card_width - 36, 246))
            write(draw, (x + 20, y + 382), caption, sans(24),
                  MUTED, card_width - 40)
        save(im, name, {"columns": columns, "rows": rows, "steps": 4})

    def versions(width, columns, name):
        pad = 44 if width == 1600 else 40
        gap = 24
        card_width = (width - pad * 2 - gap * (columns - 1)) // columns
        panel_height = int((card_width - 36) * 326 / 410)
        card_height = 78 + panel_height + 22
        rows = math.ceil(len(VERSIONS) / columns)
        height = 136 + rows * card_height + (rows - 1) * gap + 32
        im, draw, _ = board(width, height, "六个版本，从观测到行动",
                            "每格上方为模型，下方为对应输入")
        with Image.open(source / "docs/readme/asset-iterations.png") as original:
            assert original.size == (1440, 1000)
            for i, (version, purpose) in enumerate(VERSIONS):
                col, row = i % 3, i // 3
                left, top = 47 + col * 468, 181 + row * 437
                # Entire retained model/input rectangle, excluding old card labels.
                panel = original.crop((left, top, left + 410, top + 326))
                x = pad + (i % columns) * (card_width + gap)
                y = 136 + (i // columns) * (card_height + gap)
                draw.rounded_rectangle((x, y, x + card_width, y + card_height),
                                       radius=14, fill=CARD, outline=LINE, width=2)
                draw.line((x + 18, y + 21, x + 18, y + 49), fill=GOLD, width=3)
                write(draw, (x + 30, y + 16), version + " / " + purpose,
                      sans(32), INK, card_width - 48)
                contain(im, panel, (x + 18, y + 78,
                                   card_width - 36, panel_height))
        save(im, name, {"columns": columns, "rows": rows,
                        "versions": [x[0] for x in VERSIONS]})

    def pair(width, columns, name):
        pad = 44 if width == 1600 else 40
        gap = 24
        card_width = (width - pad * 2 - gap * (columns - 1)) // columns
        photo_height = int((card_width - 36) * 9 / 16)
        card_height = 76 + photo_height + 22
        rows = math.ceil(len(PAIR) / columns)
        height = 136 + rows * card_height + (rows - 1) * gap + 32
        im, draw, _ = board(width, height, "看模型，也看机器人怎样走",
                            "官方查看器中的原模型 / 原场景中的独立行动")
        for i, (label, relative) in enumerate(PAIR):
            x = pad + (i % columns) * (card_width + gap)
            y = 136 + (i // columns) * (card_height + gap)
            draw.rounded_rectangle((x, y, x + card_width, y + card_height),
                                   radius=14, fill=CARD, outline=LINE, width=2)
            write(draw, (x + 20, y + 17), label, sans(32),
                  INK, card_width - 40)
            with Image.open(source / relative) as picture:
                assert picture.size == (1920, 1080)
                contain(im, picture, (x + 18, y + 76,
                                     card_width - 36, photo_height))
        save(im, name, {"columns": columns, "rows": rows, "images": 2})

    flow(1600, 4, "flow-desktop.png")
    flow(800, 2, "flow-mobile.png")
    pair(1600, 2, "model-action-desktop.jpg")
    pair(800, 1, "model-action-mobile.jpg")
    versions(1600, 3, "versions-desktop.png")
    versions(800, 2, "versions-mobile.png")

    # These directly reused images remain byte-for-byte originals in the README.
    reused = [original_files["docs/readme/photo-to-model.gif"],
              original_files["docs/readme/viewer.jpg"],
              original_files["docs/readme/robot-action.jpg"]]
    game_image = "evidence/judges-demo/figures/05-M20-leg-action.jpg"
    game_manifest = json.loads((source / "evidence/judges-demo/manifest.json").read_text())
    material = game_manifest["editor_material"]
    jpeg = next(x for x in material["files"] if x["file"] == "05-M20-leg-action.jpg")
    still = next(x for x in material["stills"] if x["file"] == "05-M20-leg-action.png")
    game_check = checked(game_image, jpeg["sha256"])
    reused.append({"path": game_image, "sha256": sha(game_check),
                   "bytes": game_check.stat().st_size,
                   "source_manifest": "evidence/judges-demo/manifest.json",
                   "source_video": still["source"],
                   "code_commit": still["code_commit"],
                   "video_time_s": still["video_seconds"],
                   "note": "2026-11-18 native recording frame; M20 display appearance."})
    manifest = {
        "schema": "beforestep-readme-showcase/v1",
        "purpose": "A complete visual project entrance with real assets and narrow-screen layouts.",
        "palette": {"paper": PAPER, "card": CARD, "ink": INK,
                    "muted": MUTED, "gold": GOLD},
        "responsive": {"media": "(max-width: 600px)", "desktop_width": 1600,
                       "mobile_width": 800,
                       "note": "GitHub Markdown preserves picture/source; each desktop/mobile image uses the same retained sources."},
        "source_checks": list(source_checks.values()),
        "files": files,
        "reused_images": reused,
        "flow": {"sources": [{"label": label, "title": title, "path": relative,
                             "sha256": expected}
                            for label, title, _, relative, expected in FLOW],
                 "photo_and_model_task": 5958685,
                 "twelve_worlds": evidence_manifest["twelve_worlds"],
                 "grid_panel_rectangle": list(GRID_RECT),
                 "grid_note": "Only the evidence panel's added paper title/footer are removed. The whole 4x3 twelve-world video frame is retained."},
        "versions": {"source": original_files["docs/readme/asset-iterations.png"],
                     "upstream_manifest": "evidence/award/asset-iterations/manifest.json",
                     "source_rectangles": [
                         {"version": version, "rectangle": [
                             47 + (i % 3) * 468, 181 + (i // 3) * 437,
                             457 + (i % 3) * 468, 507 + (i // 3) * 437]}
                         for i, (version, _) in enumerate(VERSIONS)],
                     "note": "Each complete retained model/input rectangle is fitted with one uniform scale; no model or input is reconstructed."},
        "pair": {"movie": old_manifest["movie_source"],
                 "snapshot_seconds": old_manifest["snapshot_seconds"],
                 "display": "Both original 16:9 screenshots are fitted whole, without cropping."},
        "fonts": [{"name": args.sans.name, "sha256": sha(args.sans)},
                  {"name": args.serif.name, "sha256": sha(args.serif)}],
        "font_credits": "docs/credits.md",
        "retained_visual_manifest": SOURCE_MANIFEST,
        "retained_evidence_manifest": EVIDENCE_MANIFEST,
        "new_generation_tasks": 0,
        "new_physics_runs": 0,
        "image_handling": "Contain and whole source-panel extraction only; no recoloring, stretching or fabricated geometry.",
    }
    (out / "sources.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    # Text positions are checked during building; bounds are not added to the
    # public manifest because they do not describe experiment or asset provenance.
    print(json.dumps({"output": str(out), "images": len(files),
                      "bytes": sum(x["bytes"] for x in files),
                      "source_checks": len(source_checks),
                      "text_labels_checked": len(text_bounds)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
