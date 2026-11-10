"""Audit preserved same-input Lux3D tasks; no generation or simulation calls."""
from itertools import combinations
from pathlib import Path
import hashlib
import json
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from beforestep.navigation import map as N

OBS = "assets/observations/trained_live_gate_001/looks"
GEOMETRY = (
    "evidence/learning/geometry/"
    "0127c83bdf403e44d6a36580bd773c10e9cddc396def70caf388b52b1e21b7e1/T1"
)
OUT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def main():
    sources = {}

    def tracked(path):
        sources[path] = sha(path)
        return ROOT / path

    def read_json(path):
        return json.loads(tracked(path).read_text())

    request = read_json(f"{OBS}/look1/T1/lux_request.json")
    result = read_json(f"{OBS}/look1/T1/lux_result.json")
    decision = read_json(f"{GEOMETRY}/target_decision.json")
    state = np.load(tracked(f"{OBS}/look1_state.npy"), allow_pickle=False)
    tracked("src/beforestep/navigation/map.py")
    tracked(str(Path(__file__).relative_to(ROOT)))
    unknown = np.isin(state, [N.DARK, N.HIDDEN, N.UNSEEN])
    candidates = {c["id"]: c for c in decision["candidates"]}
    items = {item["id"]: item for item in request["items"]}
    groups, seen_tasks, footprints = {}, set(), {}
    for task in result["tasks"]:
        task_id = task["task_id"]
        if task_id in seen_tasks:
            raise ValueError(f"Duplicate task ID: {task_id}")
        seen_tasks.add(task_id)
        item = items[task["id"]]
        inputs = task["inputs"]
        hashes = [sha(tracked(path).relative_to(ROOT)) for path in inputs]
        if hashes != task["input_sha256"] or hashes != [item["sha256"]]:
            raise ValueError(f"Input identity mismatch: {task_id}")
        key = (request["mode"], request["version"], request["faceCount"], tuple(hashes))
        group = groups.setdefault(key, {"mode": key[0], "version": key[1],
            "faceCount": key[2], "ordered_input_sha256": hashes, "tasks": []})
        entry = {"id": task["id"], "task_id": task_id, "status": task["status"]}
        if task["status"] == "ok":
            digest = sha(tracked(task["glb"]).relative_to(ROOT))
            if digest != task["glb_sha256"]:
                raise ValueError(f"GLB identity mismatch: {task_id}")
            c = candidates[task["id"]]
            entry.update({"glb": task["glb"], "glb_sha256": digest,
                "admitted": c["admitted"], "metrics": {k: c[k] for k in
                ("contour_iou", "scale_ratio", "hidden_frac", "shell_contact",
                 "free_intrusion_frac")}})
            path = f"{GEOMETRY}/footprint_{task['id']}.npy"
            footprint = np.load(tracked(path), allow_pickle=False)
            if footprint.dtype != bool or footprint.shape != state.shape:
                raise ValueError(f"Unexpected footprint: {path}")
            footprints[task["id"]] = footprint
        group["tasks"].append(entry)

    for group in groups.values():
        tasks = group["tasks"]
        group.update({"submitted": len(tasks),
            "generated": sum(t["status"] == "ok" for t in tasks),
            "admitted": sum(t.get("admitted", False) for t in tasks), "pairs": []})
        generated = [t for t in tasks if t["status"] == "ok"]
        for left, right in combinations(generated, 2):
            a, b = footprints[left["id"]], footprints[right["id"]]
            union = int(((a | b) & unknown).sum())
            intersection = int(((a & b) & unknown).sum())
            changed = int(((a ^ b) & unknown).sum())
            group["pairs"].append({"ids": [left["id"], right["id"]],
                "both_admitted": left["admitted"] and right["admitted"],
                "all_map_different_cells": int((a ^ b).sum()),
                "unknown_occupied_cells": [int((a & unknown).sum()), int((b & unknown).sum())],
                "unknown_intersection_cells": intersection, "unknown_union_cells": union,
                "unknown_different_cells": changed,
                "unknown_disagreement_area_m2": changed * N.RES ** 2,
                "unknown_footprint_iou": intersection / union if union else None})

    audit = {"schema": "beforestep-same-input-audit/v1",
        "scope": "All six preserved trained_live_gate_001 tasks; one observed rock, three input cohorts",
        "geometry_identity": decision["cache_identity"], "thresholds": decision["thresholds"],
        "map": {"resolution_m": N.RES, "shape": list(state.shape),
            "unknown_labels": ["DARK", "HIDDEN", "UNSEEN"]},
        "groups": list(groups.values()), "sources_sha256": dict(sorted(sources.items())),
        "limitations": [
            "Independent task IDs do not establish statistically independent or calibrated posterior samples.",
            "Unknown map cells include shadow and occlusion; they are not a back-face-only segmentation.",
            "World occupancy differences include generation, registration and grid discretization effects.",
            "The two admitted same-input samples do not establish hazard coverage, cliff geometry or safety gains.",
            "Existing admission results are audited, not recalibrated or rerun here."]}
    (OUT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    build_figure(state, footprints["C1"], footprints["C2"], unknown, items["C1"]["path"])
    print(json.dumps({"submitted": len(seen_tasks), "cohorts": len(groups),
        "pairs": [p for g in groups.values() for p in g["pairs"]],
        "output": str(OUT.relative_to(ROOT))}, indent=2))


def build_figure(state, a, b, unknown, input_path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    from matplotlib.patches import Patch

    indices = np.argwhere(a | b)
    lo = np.maximum(indices.min(axis=0) - 5, 0)
    hi = np.minimum(indices.max(axis=0) + 6, state.shape)
    region = np.s_[lo[0]:hi[0], lo[1]:hi[1]]
    extent = [N.X0 + lo[0] * N.RES, N.X0 + hi[0] * N.RES,
              N.Y0 + lo[1] * N.RES, N.Y0 + hi[1] * N.RES]
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.5), constrained_layout=True)
    axes[0].imshow(plt.imread(ROOT / input_path))
    axes[0].set_title("Identical uploaded image (C1 / C2)")
    axes[0].axis("off")
    colors = ["#fafafa", "#444444", "#ddd6c8", "#e4e6eb", "#f0f1f4", "#888888"]
    axes[1].imshow(state[region].T, origin="lower", extent=extent,
                   cmap=ListedColormap(colors), vmin=0, vmax=5, interpolation="nearest")
    for footprint, color, label in ((a, "#2466b6", "C1"), (b, "#ed8a23", "C2")):
        axes[1].contour(N.XS[lo[0]:hi[0]], N.YS[lo[1]:hi[1]], footprint[region].T,
                        levels=[0.5], colors=[color], linewidths=1.6)
        axes[1].plot([], [], color=color, label=label)
    axes[1].set_title("Registered navigation footprints")
    axes[1].legend(loc="lower right")
    differences = np.zeros_like(state)
    differences[(a & ~b) & unknown] = 1
    differences[(b & ~a) & unknown] = 2
    axes[2].imshow(differences[region].T, origin="lower", extent=extent,
                   cmap=ListedColormap(["#fafafa", "#2466b6", "#ed8a23"]),
                   vmin=0, vmax=2, interpolation="nearest")
    count = int(((a ^ b) & unknown).sum())
    axes[2].set_title(f"Unknown-region disagreement: {count} cells")
    axes[2].legend(handles=[Patch(color="#2466b6", label="C1 only"),
                            Patch(color="#ed8a23", label="C2 only")], loc="lower right")
    for axis in axes[1:]:
        axis.set_xlabel("World x (m)")
        axis.set_ylabel("World y (m)")
        axis.set_aspect("equal")
    fig.suptitle("Two admitted same-input samples; 5 cm grid; hazard coverage unverified", fontsize=12)
    fig.savefig(OUT / "comparison.png", dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    main()
