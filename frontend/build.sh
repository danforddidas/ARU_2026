#!/usr/bin/env bash
set -o errexit
BACKEND_URL="${BACKEND_URL:-http://127.0.0.1:8000}"
python - <<'PY'
from pathlib import Path
import os
url=os.environ.get("BACKEND_URL","http://127.0.0.1:8000").rstrip("/")
Path("assets/config.js").write_text(f'window.APP_CONFIG = {{ API_BASE_URL: "{url}/api" }};\n',encoding="utf-8")
PY
