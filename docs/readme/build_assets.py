"""Build the README visuals from the retained photo, models and Demo."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from PIL import Image, ImageDraw, ImageFont, ImageOps

MOVIE_COMMIT = "ab537d62c075c4d7be1e829cecb69a4708258221"
MOVIE_PATH = "evidence/lux3d-demo-v2/BeforeStep-Lux3D-Demo-v2.mp4"
MOVIE_SHA = "f5d36f6a113e0558a78cee963214186b79f9dfea716dc8b3d089672841de0870"
ITERATIONS_PATH = "evidence/production-v6/figures/six-version-assets.png"
ITERATIONS_SHA = "eb497dc4f14668f205ec27135f2e82db78f336046d5eb9e1aafba82d75984cae"
BACKGROUND = "#10171d"
TEXT = "#e8e7df"
MUTED = "#a7b7be"
GOLD = "#e6b976"
CARDS = [
    ("01 / 机器人拍照", "一张石头照片",
     "site/media/real-footage/r1-task-5958685-input.jpg",
     "36c6920301bb5aee1a23970af7b9229a100ee42ffb0aa70f9e84edd61c2aa5cd",
     ["机器人获得原始观测", "把石头照片交给 Lux3D"]),
    ("02 / Lux3D 生成", "整块石头的 3D",
     "site/media/home-lux3d/model-5958685.jpg",
     "feadecd1eefa082eb473208558224b77f7bd81426282e9cff5ed8e3ffe638461",
     ["返回可以旋转的模型", "补出照片看不到的形状"]),
    ("03 / BeforeStep 预演", "在模型里走一遍",
     "site/media/home-lux3d/rehearsal.jpg",
     "cfc66a7f3c39838bdbf254639e227234629c2a1229c631c5da78ab87e0fd8b00",
     ["对照观测、组合模型世界", "预演同一条候选路线"]),
    ("04 / 机器人行动", "选择走、看或停",
     "site/media/home-lux3d/action.jpg",
     "3d544b4353b613f7d8596e35fc417fe14ab51bee02885d6138a925100708f6c3",
     ["使用各个世界的预演结果", "在原场景中选择行动"]),
]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_source(path, expected):
    if sha(path) != expected:
        raise ValueError(f"Source bytes differ: {path}. Fetch its Git LFS content.")


def run_ffmpeg(arguments):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *arguments], check=True)


def make_iterations(source, output, font_path):
    """Keep the six original model/input panels and label each version's role."""
    board = Image.new("RGB", (1440, 1000), BACKGROUND)
    draw = ImageDraw.Draw(board)
    font = lambda size: ImageFont.truetype(str(font_path), size)
    draw.text((32, 22), "六个版本 · 从观测到行动", font=font(34), fill=TEXT)
    draw.text((32, 70), "每格上方为模型，下方为对应输入", font=font(21), fill=MUTED)
    versions = [
        ("V6", "观测约束融合"), ("V7", "双视角与模型核对"),
        ("V8", "窄道里的候选模型"), ("v0.1", "模块化检查与预演"),
        ("v0.2", "关口中的完整通行"), ("v0.3", "训练模型控制动作"),
    ]
    with Image.open(source) as original:
        for i, (version, purpose) in enumerate(versions):
            col, row = i % 3, i // 3
            x, y = 28 + col * 468, 116 + row * 437
            draw.rounded_rectangle((x, y, x + 448, y + 417), radius=12,
                                   fill="#19232b", outline="#3b4b57", width=2)
            draw.text((x + 18, y + 12), version + " · " + purpose,
                      font=font(22), fill=GOLD)
            left = [47, 516, 983][col]
            top = 198 if row == 0 else 666
            panel = original.crop((left, top, left + 410, top + 326)).convert("RGB")
            board.paste(panel, (x + 19, y + 65))
    board.save(output, optimize=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--out", type=Path, default=Path("outputs/readme-assets"))
    parser.add_argument("--movie", type=Path, help="Local copy of the same verified film")
    parser.add_argument("--font", type=Path,
                        default=Path("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"))
    args = parser.parse_args()
    repo = args.repo.resolve()
    out = args.out.resolve()
    movie = args.movie or repo / MOVIE_PATH
    check_source(movie, MOVIE_SHA)
    check_source(repo / ITERATIONS_PATH, ITERATIONS_SHA)
    for _, _, relative, digest, _ in CARDS:
        check_source(repo / relative, digest)
    if not args.font.is_file():
        raise FileNotFoundError(f"Chinese font missing; pass --font: {args.font}")
    if out.exists():
        raise FileExistsError(f"Choose a new output directory: {out}")
    out.mkdir(parents=True)

    run_ffmpeg([
        "-filter_complex_threads", "1", "-threads", "2", "-ss", "4.1", "-t", "7.8",
        "-i", str(movie), "-filter_complex",
        "[0:v]fps=8,scale=900:-1:flags=lanczos,split[a][b];"
        "[a]palettegen=max_colors=96:stats_mode=diff[p];"
        "[b][p]paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle",
        "-an", "-loop", "0", str(out / "photo-to-model.gif"),
    ])
    for name, seconds in [("viewer", 35), ("robot-action", 84)]:
        run_ffmpeg(["-ss", str(seconds), "-i", str(movie), "-frames:v", "1",
                    "-q:v", "2", str(out / (name + ".jpg"))])
    make_iterations(repo / ITERATIONS_PATH, out / "asset-iterations.png", args.font)

    font = lambda size: ImageFont.truetype(str(args.font), size)
    flow = Image.new("RGB", (1600, 560), BACKGROUND)
    draw = ImageDraw.Draw(flow)
    draw.text((40, 22), "Lux3D 提供完整形状，模型进入后续判断", font=font(34), fill=TEXT)
    sources = []
    for i, (label, title, relative, digest, lines) in enumerate(CARDS):
        x = 40 + i * 390
        draw.rounded_rectangle((x, 88, x + 350, 523), radius=15, fill="#19232b",
                               outline="#3b4b57", width=2)
        draw.text((x + 20, 104), label, font=font(21), fill=GOLD)
        draw.text((x + 20, 140), title, font=font(30), fill=TEXT)
        with Image.open(repo / relative) as source:
            thumb = ImageOps.contain(source.convert("RGB"), (310, 230),
                                     method=Image.Resampling.LANCZOS)
            flow.paste(thumb, (x + 20 + (310 - thumb.width) // 2,
                               194 + (230 - thumb.height) // 2))
        for j, line in enumerate(lines):
            draw.text((x + 20, 442 + j * 32), line, font=font(22), fill=MUTED)
        if i < 3:
            draw.line((x + 357, 310, x + 382, 310), fill=GOLD, width=3)
            draw.polygon([(x + 382, 310), (x + 373, 303), (x + 373, 317)], fill=GOLD)
        sources.append({"image": relative, "sha256": digest, "use": label})
    flow.save(out / "model-to-decision.png", optimize=True)

    badges = out / "badges"
    badges.mkdir()
    for name, label, value, width, split in [
        ("lux3d", "Aholo Lux3D", "照片 → 3D", 240, 124),
        ("viewer", "Aholo Viewer", "官方模型查看器", 280, 130),
        ("mujoco", "MuJoCo", "仿真实录", 215, 92),
    ]:
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="29" '
            f'role="img" aria-label="{label}: {value}">'
            f'<rect width="{width}" height="29" rx="5" fill="#1d2a34"/>'
            f'<path d="M{split} 0H{width-5}Q{width} 0 {width} 5V24Q{width} 29 '
            f'{width-5} 29H{split}Z" fill="#d8b276"/>'
            '<g font-family="Arial,Microsoft Yahei,sans-serif" font-size="12" '
            'text-anchor="middle">'
            f'<text x="{split/2}" y="19" fill="#ebeeee">{label}</text>'
            f'<text x="{split+(width-split)/2}" y="19" fill="#1b2429">{value}</text>'
            '</g></svg>'
        )
        (badges / (name + ".svg")).write_text(svg + "\n")

    manifest = {
        "scope": "README visual explanation from existing real assets",
        "movie_source": {"path": MOVIE_PATH, "commit": MOVIE_COMMIT, "sha256": MOVIE_SHA},
        "GIF_excerpt": {"start_s": 4.1, "duration_s": 7.8, "fps": 8,
                        "purpose": "Show the real robot photo and corresponding returned model, "
                                   "with actual official viewer imagery."},
        "snapshot_seconds": {"viewer.jpg": 35, "robot-action.jpg": 84},
        "flow_sources": sources,
        "asset_iterations_source": {"path": ITERATIONS_PATH, "sha256": ITERATIONS_SHA},
        "asset_iterations_layout": "Six retained model/input panels with version-role titles",
        "files": [{"path": "docs/readme/" + str(p.relative_to(out)),
                   "sha256": sha(p), "bytes": p.stat().st_size}
                  for p in sorted(out.rglob("*")) if p.is_file()],
        "new_generation_tasks": 0,
        "new_physics_runs": 0,
    }
    (out / "sources.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(f"Built {len(manifest['files'])} visual assets in {out}")


if __name__ == "__main__":
    main()
