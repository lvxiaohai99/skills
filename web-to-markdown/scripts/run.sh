#!/usr/bin/env bash
# 自包含运行入口:首次调用时在 skill 目录内创建 .venv 并安装依赖,
# 之后直接复用。把所有参数透传给 web_to_md.py。
#
# 用法:
#   run.sh <url> [url ...] [-d 输出目录]
#   run.sh -f urls.txt -d 输出目录
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$SKILL_DIR/.venv"
PY="$VENV/bin/python"

if [ ! -x "$PY" ]; then
  echo "[setup] 首次运行,创建虚拟环境并安装依赖..." >&2
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install -q --upgrade pip >&2
  "$VENV/bin/pip" install -q -r "$SKILL_DIR/requirements.txt" >&2
fi

exec "$PY" "$SKILL_DIR/scripts/web_to_md.py" "$@"
