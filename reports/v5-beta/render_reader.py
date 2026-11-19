#!/usr/bin/env python3
"""Render the owner-provided V5 Beta PDF without changing its original bytes."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path

import pymupdf
from PIL import Image


EXPECTED_SHA = "fe2ff9b9356202760254cc29deadfa1e963986d69c7c0f1ee39b9ab0764d1cb7"
LABELS = ["封面", "问题起点", "理论依据与双线交汇", "实现链路", "可信度", "多场景测试", "轮腿执行", "边界", "过程与关键资产", "在线交互体验", "附录与参考"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--expected-sha256", default=EXPECTED_SHA)
    args = parser.parse_args()
    repo = args.repo.resolve()
    data = args.source.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    assert data.startswith(b"%PDF-") and digest == args.expected_sha256, "V5 Beta source identity differs"
    output = repo / "site/media/report-v5-beta"
    report = repo / "reports/v5-beta"
    output.mkdir(parents=True, exist_ok=True)
    report.mkdir(parents=True, exist_ok=True)
    (report / "report.pdf").write_bytes(data)
    (output / "report.pdf").write_bytes(data)
    pages = []
    with pymupdf.open(args.source) as document:
        assert len(document) == len(LABELS), "Check headings against the supplied report before rendering"
        for n, page in enumerate(document, 1):
            pixmap = page.get_pixmap(matrix=pymupdf.Matrix(1200 / page.rect.width, 1200 / page.rect.width), alpha=False)
            image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
            filename = f"page-{n:02}.jpg"
            target = output / filename
            image.save(target, quality=88, optimize=True, subsampling=0)
            pages.append({"page": n, "title": LABELS[n - 1], "path": target.relative_to(repo).as_posix(), "width": image.width, "height": image.height, "sha256": hashlib.sha256(target.read_bytes()).hexdigest(), "bytes": target.stat().st_size})
    manifest = {
        "schema": "beforestep-report-v5-beta/v1", "version": "V5 Beta", "page_count": len(pages),
        "owner_original": {"path": "reports/先见一步_项目报告书_v5_beta.pdf", "commit": "33d7dfe1ce1a43c5ea6cc3f72f8b2ec5fb509511", "sha256": digest, "bytes": len(data)},
        "repository_pdf": "reports/v5-beta/report.pdf", "website_pdf": "site/media/report-v5-beta/report.pdf", "pages": pages,
        "method": "The exact owner PDF is copied byte for byte. Reading images render whole pages at width 1200; PDF content is not rewritten.",
        "runtime_scope": "The PDF preserves the author's V5 Beta snapshot. Current first-judgment choices, full materials and native-footage delivery are documented separately in docs/mission.md and docs/judges-demo.md.",
    }
    (report / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    options = "".join(f'<option value="{p["page"]}">第 {p["page"]} 页 · {html.escape(p["title"])}</option>' for p in pages)
    toc = "".join(f'<a href="#page-{p["page"]}" data-page-link="{p["page"]}"><span>{p["page"]:02}</span>{html.escape(p["title"])}</a>' for p in pages)
    figures = "".join(
        f'<figure class="page" id="page-{p["page"]}"><img src="media/report-v5-beta/page-{p["page"]:02}.jpg" width="{p["width"]}" height="{p["height"]}" alt="项目报告书 V5 Beta，第 {p["page"]} 页：{html.escape(p["title"])}" loading="{"eager" if p["page"] == 1 else "lazy"}" decoding="async"><figcaption><span>第 {p["page"]} / {len(pages)} 页 · {html.escape(p["title"])}</span><a href="media/report-v5-beta/report.pdf#page={p["page"]}" target="_blank" rel="noopener">在 PDF 中放大看 ↗</a></figcaption></figure>'
        for p in pages
    )
    template = '''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>项目报告书 V5 Beta · 先见一步</title><meta name="description" content="负责人提供的先见一步 V5 Beta 主报告，11页原稿逐页阅读与原PDF下载；当前玩法、原片与研究来源分别可查。"><link rel="icon" href="favicon.svg"><link rel="stylesheet" href="site-chrome.css?v=v5beta-20261119"><link rel="stylesheet" href="report-v3.css?v=v5beta-20261119"><script defer src="report-reader.js?v=v5beta-20261119"></script><link rel="preload" href="fonts/beforestep-serif-bold.woff2" as="font" type="font/woff2" crossorigin><link rel="preload" href="fonts/beforestep-sans-regular.woff2" as="font" type="font/woff2" crossorigin><link rel="stylesheet" href="report-look.css?v=v5beta-20261119"></head>
<body class="report-page report-look"><a class="skip-link" href="#main">跳到内容</a><header class="site-chrome"><a class="chrome-brand" href="index.html"><span class="brand-symbol" aria-hidden="true">✦</span><span class="brand-name">先见一步<small>BEFORESTEP / NEXT ZENITH</small></span></a><nav aria-label="主要导航"><a href="index.html">认识作品</a><a href="play.html">操作机器人</a><a href="gallery.html">模型陈列室</a><a href="levels.html">实验回放</a><a href="report.html" aria-current="page">项目报告</a></nav></header>
<main id="main" class="page-shell"><section class="report-intro"><div><p class="eyebrow">当前主报告 / V5 Beta · 负责人原稿</p><h1>先见一步，<br>从空间先验到行动。</h1><p>11 页报告，说明 Lux3D 三维先验怎样进入局部空间建模、观测核对和物理预演，以及轮腿探索的结果与边界。</p><div class="report-actions"><a class="primary" href="media/report-v5-beta/report.pdf" download="先见一步_项目报告书_v5_beta.pdf">下载 V5 Beta 报告 <span>PDF · 7.7 MB ↗</span></a><a href="media/report-v5-beta/report.pdf" target="_blank" rel="noopener">打开 PDF ↗</a><a href="https://www.bilibili.com/video/BV1YZst6eEZk/" target="_blank" rel="noopener">B站主宣传片 ↗</a></div><p class="reader-note">报告原件按原字节保留。当前试玩的初判后自主选择与最新原片，另见<a href="https://github.com/codezzzsleep/next-zenith-beforestep/blob/main/docs/current-status.md">当前交付说明</a>。</p></div><a class="report-cover" href="#page-1" data-page-link="1"><img src="media/report-v5-beta/page-01.jpg" width="1200" height="1698" alt="主报告书 V5 Beta 封面"><span>先见一步 · 项目报告书 V5 Beta</span></a></section>
<div class="report-mobile-nav"><label for="report-page-select">跳转到</label><select id="report-page-select">__OPTIONS__</select><span id="report-mobile-progress">1 / 11</span></div><div class="report-body"><aside class="report-toc"><p class="eyebrow">阅读目录</p><nav aria-label="报告页码">__TOC__</nav><div class="reader-progress"><span id="report-progress">第 1 / 11 页</span><div><button id="report-prev" disabled aria-label="上一页">←</button><button id="report-next" aria-label="下一页">→</button></div></div><p class="reader-note">按目录直达一页，原 PDF 可放大查看。</p></aside><section class="report-pages" aria-label="正式报告逐页阅读">__PAGES__</section></div>
<section class="report-resources"><div><p class="eyebrow">读完之后，继续复查</p><h2>当前试玩、原片，<br>以及每一步的来源。</h2><p>报告、原研究和当前交互版本分别保留身份，来源与边界可对照查阅。</p></div><div><details><summary>当前试玩与连续 1080p 原片</summary><p><a href="play.html">亲自操作月面任务</a> · <a href="https://github.com/codezzzsleep/next-zenith-beforestep/releases/tag/judges-demo-20261118">下载连续母片、清晰补拍与五图</a> · <a href="https://github.com/codezzzsleep/next-zenith-beforestep/blob/main/docs/mission.md">当前操作说明</a></p><p>初判后可自选手控、想象、补看或停车；辅助路线须通过所选世界的真实预演。原片是导演剪辑素材，最终112秒成片另行制作。</p></details><details><summary>报告原件、历史版本与研究来源</summary><p><a href="https://github.com/codezzzsleep/next-zenith-beforestep/blob/main/reports/v5-beta/manifest.json">V5 Beta 原文件与逐页 SHA</a> · <a href="https://github.com/codezzzsleep/next-zenith-beforestep/blob/main/reports/README.md">报告版本索引</a> · <a href="media/report.pdf">V3 原 PDF</a> · <a href="media/report-v5/report.pdf">旧 V5 原 PDF</a> · <a href="https://github.com/codezzzsleep/next-zenith-beforestep/blob/main/reports/v4/report.pdf">V4 历史 PDF</a></p><p><a href="https://github.com/codezzzsleep/next-zenith-beforestep/blob/main/docs/code-tour.md">源码与冻结R1复现</a> · <a href="https://github.com/codezzzsleep/next-zenith-beforestep/blob/main/docs/history/site/report-before-v3.html">历史完整技术报告源码</a> · <a href="https://github.com/codezzzsleep/next-zenith-beforestep/blob/main/evidence/production-v6/facts.json">研究事实与累计任务节点</a></p></details></div></section></main><footer class="site-footer page-shell"><div><strong>先见一步 · BeforeStep</strong><p>Next Zenith / Aholo 全球 3D AI 黑客松作品</p></div><p><a href="report.html">主报告 V5 Beta</a> · <a href="https://github.com/codezzzsleep/next-zenith-beforestep">源码与复现 ↗</a><br>机器人运动为 MuJoCo 仿真，三维模型来自真实 Lux3D 返回。</p></footer></body></html>
'''
    text = template.replace("__OPTIONS__", options).replace("__TOC__", toc).replace("__PAGES__", figures)
    # The existing portrait styling is retained; rendered page dimensions come from the actual PDF.
    text = text.replace('width="1200" height="1698" alt="主报告书 V5 Beta 封面"', f'width="{pages[0]["width"]}" height="{pages[0]["height"]}" alt="主报告书 V5 Beta 封面"')
    for filename in ("report.html", "project-report.html"):
        (repo / "site" / filename).write_text(text)
    print(json.dumps({"version": "V5 Beta", "pages": len(pages), "pdf_sha256": digest, "pdf_bytes": len(data), "reading_image_bytes": sum(p["bytes"] for p in pages)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
