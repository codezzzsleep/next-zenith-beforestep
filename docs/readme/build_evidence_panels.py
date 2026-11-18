#!/usr/bin/env python3
"""Compose homepage evidence from retained R1 images and recorded frames."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


SIZE = (1600, 900)
PAPER = "#f6f3ec"
INK = "#1c304b"
MUTED = "#66717d"
SUCCESS = "#287364"
FAILURE = "#b44c43"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--source-root", type=Path, help="Checkout containing retained binary payloads")
    parser.add_argument("--world-grid", type=Path, required=True, help="Original four-by-three R1 recording")
    parser.add_argument("--font", type=Path, required=True, help="CJK font file")
    args = parser.parse_args()
    repo = args.repo.resolve()
    source = (args.source_root or repo).resolve()
    fonts = {n: ImageFont.truetype(str(args.font), n) for n in (26, 32, 38, 52)}
    target = repo / "site/media/home-evidence-20261118"
    target.mkdir(parents=True, exist_ok=True)
    input_path = Path("evidence/reviews/beforestep_r1/lux/original_b/looks/look1/T2/gen/variants/A1_upload.jpg")
    results_path = Path("evidence/reviews/beforestep_r1/lux/original_b/looks/look1/T2/lux_result.json")
    decision_path = Path("evidence/reviews/beforestep_r1/lux/original_b/looks/look1/T2/decide/target_decision.json")
    tasks = json.loads((source / results_path).read_text())["tasks"]
    pair = [next(x for x in tasks if x["task_id"] == task) for task in (5958654, 5958642)]
    assert pair[0]["input_sha256"] == pair[1]["input_sha256"]
    assert sha(source / input_path) == pair[0]["input_sha256"][0]
    decisions = json.loads((source / decision_path).read_text())
    passed = next(x for x in decisions["candidates"] if x["id"] == "A2")
    refused = next(x for x in decisions["candidates"] if x["id"] == "A1")
    assert passed["admitted"] and not refused["admitted"]
    assert sha(args.world_grid) == "b10a0005b52962f8d9b8069b75f55d0c3ec1ab5e18c5557c30f00fed7aa5e762"

    def canvas(title: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
        image = Image.new("RGB", SIZE, PAPER)
        draw = ImageDraw.Draw(image)
        draw.text((42, 28), title, font=fonts[52], fill=INK)
        draw.line((42, 105, 1558, 105), fill="#d6cdbf", width=2)
        return image, draw

    def contain(image: Image.Image, box: tuple[int, int, int, int], background: str = PAPER) -> None:
        x, y, width, height = box
        thumb = ImageOps.contain(image.convert("RGB"), (width, height), Image.Resampling.LANCZOS)
        current.paste(background, (x, y, x + width, y + height))
        current.paste(thumb, (x + (width - thumb.width) // 2, y + (height - thumb.height) // 2))

    def save(name: str) -> dict:
        path = target / name
        current.save(path, quality=91, optimize=True, subsampling=0)
        return {"path": path.relative_to(repo).as_posix(), "sha256": sha(path), "bytes": path.stat().st_size, "width": 1600, "height": 900}

    files = []
    current, draw = canvas("同一眼观测，核对两份真实候选")
    columns = [42, 558, 1074]
    pictures = [input_path, Path("site/home-assets/img/poster/B-A2.jpg"), Path("site/home-assets/img/poster/B-A1.jpg")]
    labels = [("机器人原始照片", INK), ("通过观测核对", SUCCESS), ("被拒候选", FAILURE)]
    for x, path, (label, color) in zip(columns, pictures, labels):
        draw.text((x, 129), label, font=fonts[38], fill=color)
        contain(Image.open(source / path), (x, 197, 484, 484))
    draw.text((42, 720), "RGB 输入 · 两次提交同字节", font=fonts[32], fill=MUTED)
    draw.text((558, 720), "任务 5958654 · 轮廓 IoU 0.846", font=fonts[32], fill=SUCCESS)
    draw.text((1074, 720), "任务 5958642 · 轮廓 IoU 0.433", font=fonts[32], fill=FAILURE)
    draw.text((42, 834), "R1 原观测与原核对结果 · 冻结轮廓门槛 0.7068", font=fonts[26], fill=MUTED)
    files.append(save("01-observation-and-candidates.jpg"))

    with tempfile.TemporaryDirectory(prefix="beforestep-evidence-") as temp:
        temp_root = Path(temp)

        def frame(video: Path, seconds: float, name: str) -> Image.Image:
            path = temp_root / name
            subprocess.run(["ffmpeg", "-v", "error", "-ss", str(seconds), "-i", str(video), "-frames:v", "1", str(path)], check=True)
            return Image.open(path).convert("RGB")

        current, draw = canvas("让同一条路线，走完十二个世界")
        grid = frame(args.world_grid, 3, "world-grid.png")
        assert grid.size == (1920, 1080)
        contain(grid, (42, 127, 1516, 702), "#16202b")
        draw.text((42, 847), "R1 原预演 · 六份 A × 两份 B · 完整 4 × 3 十二格", font=fonts[26], fill=MUTED)
        files.append(save("02-twelve-world-rehearsals.jpg"))

        current, draw = canvas("同一条窄道，三种选择的真实结局")
        policies = [
            ("optimistic", "直接走", "1 眼 · 80.87 秒碰撞", FAILURE),
            ("conservative", "看清再走", "5 眼 · 142.20 秒停车", MUTED),
            ("imagination", "想一想再走", "1 眼 · 112.84 秒到达", SUCCESS),
        ]
        for x, (policy, label, outcome, color) in zip(columns, policies):
            draw.text((x, 128), label, font=fonts[38], fill=INK)
            video = source / f"site/media/real-footage/r1-synchronised-{policy}.mp4"
            image = frame(video, 40.5, policy + ".png")
            assert image.size == (416, 702)
            contain(image, (x, 190, 484, 583), "#e7e2d7")
            draw.text((x, 787), outcome, font=fonts[32], fill=color)
        draw.text((42, 849), "R1 原运行 · Go2W · 结果时间为仿真时钟", font=fonts[26], fill=MUTED)
        files.append(save("03-three-real-outcomes.jpg"))

    manifest = {
        "schema": "beforestep-home-evidence/v1",
        "purpose": "Three equal-size, uncropped evidence panels for homepage and README",
        "new_generation_tasks": 0,
        "new_physics_runs": 0,
        "files": files,
        "observation_check": {
            "input": {"path": str(input_path), "sha256": sha(source / input_path)},
            "tasks": [{"task_id": x["task_id"], "input_sha256": x["input_sha256"][0], "glb_sha256": x["glb_sha256"]} for x in pair],
            "decision": {"path": str(decision_path), "sha256": sha(source / decision_path)},
            "model_images": [{"path": str(x), "sha256": sha(source / x)} for x in pictures[1:]],
            "note": "Retained model display images. The admission labels and contour IoU come from the original frozen R1 decision, not an image-only re-evaluation.",
        },
        "twelve_worlds": {
            "source": "evidence/production-v6/shots/s05-world-grid.mp4",
            "source_sha256": sha(args.world_grid), "video_time_s": 3,
            "layout": {"columns": 4, "rows": 3, "worlds": 12},
            "note": "Whole original frame fitted with preserved aspect ratio; no pane omitted.",
        },
        "outcomes": [{
            "policy": policy, "source": f"site/media/real-footage/r1-synchronised-{policy}.mp4",
            "source_sha256": sha(source / f"site/media/real-footage/r1-synchronised-{policy}.mp4"),
            "video_time_s": 40.5, "simulation_time_s": seconds, "looks": looks, "result": result,
        } for policy, seconds, looks, result in [("optimistic", 80.87, 1, "collision"), ("conservative", 142.20, 5, "stop"), ("imagination", 112.84, 1, "arrival")]],
        "display": "All original image rectangles are fitted with contain; no stretching or object bounding-box rescaling.",
    }
    (target / "sources.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"output": str(target), "files": files}, ensure_ascii=False))


if __name__ == "__main__":
    main()
