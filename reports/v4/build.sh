#!/usr/bin/env bash
# Build the report from the bundled engine, images and fonts.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
REPORT_PY="${REPORT_PY:-python3}"
REPORT_OUT="${REPORT_OUT:-$HERE/out}"
export PYTHONDONTWRITEBYTECODE=1
FONTCONFIG_FILE="$("$REPORT_PY" "$HERE/tools/configure_fonts.py")"
export FONTCONFIG_FILE
"$REPORT_PY" -W ignore "$HERE/engine/scripts/doctor.py"
"$REPORT_PY" "$HERE/tools/prepare_assets.py"
"$REPORT_PY" "$HERE/tools/make_charts.py"
"$REPORT_PY" "$HERE/tools/build_spec.py"
mkdir -p "$REPORT_OUT"
"$REPORT_PY" -W ignore "$HERE/engine/scripts/engine.py" "$HERE/spec.json" "$REPORT_OUT/report.pdf"
