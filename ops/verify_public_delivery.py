#!/usr/bin/env python3
"""Check current report identity, public links, image dimensions and frozen evidence.

Works with real binary files or Git LFS pointers; never runs generation or physics.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


class Page(HTMLParser):
    def __init__(self, text: str):
        super().__init__()
        self.links: list[str] = []
        self.images: list[dict[str, str]] = []
        self.ids: list[str] = []
        self.feed(text)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {key: value for key, value in attrs if value is not None}
        for key in ("href", "src"):
            if key in attributes:
                self.links.append(attributes[key])
        if tag == "img":
            self.images.append(attributes)
        if "id" in attributes:
            self.ids.append(attributes["id"])


def identity(path: Path) -> tuple[str, int]:
    content = path.read_bytes()
    if content.startswith(b"version https://git-lfs.github.com/spec/v1\n"):
        text = content.decode("ascii")
        digest = re.search(r"^oid sha256:([a-f0-9]{64})$", text, re.M)
        size = re.search(r"^size ([0-9]+)$", text, re.M)
        if not digest or not size:
            raise ValueError(f"Invalid LFS pointer: {path}")
        return digest[1], int(size[1])
    return hashlib.sha256(content).hexdigest(), len(content)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()
    root = args.repo.resolve()
    manifest_path = root / "evidence/current-delivery-20261118/manifest.json"
    manifest = json.loads(manifest_path.read_text())
    checks: list[dict] = []

    def check(name: str, condition: bool, detail: object = None) -> None:
        checks.append({"name": name, "passed": bool(condition), "detail": detail})

    tracked = set(subprocess.check_output(["git", "-C", str(root), "ls-files"], text=True).splitlines())

    def exists(name: str) -> bool:
        if (root / name).exists() or name in tracked:
            return True
        return any(path.startswith(name.rstrip("/") + "/") for path in tracked)

    def check_link(source: str, url: str) -> None:
        parsed = urlsplit(url)
        if parsed.scheme or parsed.netloc or not parsed.path:
            return
        candidate = (root / source).parent / unquote(parsed.path)
        if parsed.path.startswith("/"):
            candidate = root / unquote(parsed.path).lstrip("/")
        candidate = candidate.resolve()
        try:
            relative = candidate.relative_to(root).as_posix()
        except ValueError:
            check("link stays in repository", False, {"source": source, "url": url})
            return
        check("local link exists", exists(relative), {"source": source, "url": url})

    check("current schema", manifest.get("schema") == "beforestep-current-delivery/v1")
    report = manifest["report"]
    check("current report is V5", report["version"] == "V5")
    for name in [report["repository_pdf"], report["website_pdf"]]:
        check("report file exists", (root / name).is_file(), name)
        if (root / name).is_file():
            digest, size = identity(root / name)
            check("exact V5 PDF identity", digest == report["sha256"] and size == report["bytes"], name)

    for record in manifest["preserved_files"]:
        path = root / record["path"]
        check("frozen file retained", path.is_file(), record["path"])
        if path.is_file():
            check("frozen SHA unchanged", identity(path)[0] == record["sha256"], record["path"])

    homepage = Page((root / "site/index.html").read_text())
    evidence_images = [image for image in homepage.images if image.get("src", "").startswith("media/home-evidence-20261118/")]
    check("three homepage evidence images", len(evidence_images) == 3)
    check("same 1600 by 900 HTML image size", all(image.get("width") == "1600" and image.get("height") == "900" for image in evidence_images))
    sources = json.loads((root / "site/media/home-evidence-20261118/sources.json").read_text())
    check("complete twelve-world frame", sources["twelve_worlds"]["layout"] == {"columns": 4, "rows": 3, "worlds": 12})
    for record in sources["files"]:
        path = root / record["path"]
        check("same evidence output dimensions", record["width"] == 1600 and record["height"] == 900, record["path"])
        check("evidence image retained", path.is_file(), record["path"])
        if path.is_file():
            digest, size = identity(path)
            check("evidence output SHA", digest == record["sha256"] and size == record["bytes"], record["path"])

    for filename in ["site/report.html", "site/project-report.html"]:
        text = (root / filename).read_text()
        page = Page(text)
        title = re.search(r"<title>(.*?)</title>", text, re.S)
        check("report page title V5", bool(title and "V5" in title[1]), filename)
        ids = [item for item in page.ids if re.fullmatch(r"page-[0-9]+", item)]
        check("report reader has all pages", ids == [f"page-{n}" for n in range(1, report["pages"] + 1)], filename)
        pictures = [image for image in page.images if image.get("src", "").startswith("media/report-v5/page-")]
        check("report reader uses V5 images", len(pictures) == report["pages"] + 1, filename)

    for document in manifest["current_documents"]:
        path = root / document
        check("current document exists", path.is_file(), document)
        if not path.is_file():
            continue
        text = path.read_text()
        for match in re.finditer(r"!?\[[^\]]*\]\(([^\s)]+)(?:\s+[^)]*)?\)", text):
            check_link(document, match[1])
        for url in Page(text).links:
            check_link(document, url)

    readme = (root / "README.md").read_text()
    check("README current report label", "主报告 V5" in readme and "主报告 V3" not in readme)
    check("manual choice documented", "手控独立开放" in readme and "辅助路线" in readme and "预演" in readme)
    settings = json.loads((root / ".github/repository-settings.json").read_text())
    check("GitHub report version", settings["current_report_version"] == report["version"])
    check("Pages existing branch retained", settings["pages_source"] == {"branch": "gh-pages", "path": "/"})
    check("no new generation", manifest["new_generation_tasks"] == 0 and sources["new_generation_tasks"] == 0)

    failures = [item for item in checks if not item["passed"]]
    result = {"passed": not failures, "checks": len(checks), "failures": failures, "report": {"version": report["version"], "sha256": report["sha256"], "pages": report["pages"]}}
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if not failures else 1)


if __name__ == "__main__":
    main()
