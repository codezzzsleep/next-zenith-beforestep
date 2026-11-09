# Optional GitHub Actions templates

The source repository includes local runtime/evidence checks. These workflow
files can be copied into `.github/workflows` when using a GitHub credential with
workflow write permission.

The delivered showcase uses the `gh-pages` branch with ordinary binary assets
and `.nojekyll`. This lets GitHub Pages serve actual GLB/video files without LFS
pointer files. Main retains the authoritative source and full curated evidence.

`python ops/export_site.py --out /tmp/beforestep-public-site` exports the viewer,
its GLBs and model downloads, and linked JSON results. Full training snapshots,
physical meshes and trajectories remain in the source repository and release
ZIP; the hosted viewer does not request those files.
