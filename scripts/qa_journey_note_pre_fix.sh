#!/usr/bin/env bash
# PR #243 browser regression gate: identical fixture and JS, PRE vs FIX.
# Prereqs: Python requirements plus verified E2B Playwright CLI/Chromium
# (see evidence/arena-tooling-20261030/README.md). No app/production writes.
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
PRE=4dd3cb9aceaedf66a2128b8612a38012f3e13e50
FIX=6b95af35e94ef331bdf29403d1285bd77fc8c461
PY="${PYTHON_BIN:-python3}"
CLI="${PWCLI_BIN:-/tmp/pw-cli/node_modules/.bin/playwright-cli}"
CHROME="${PLAYWRIGHT_MCP_EXECUTABLE_PATH:-/tmp/chromium}"
FLOW="$ROOT/tests/component/browser_g15_customer_send_reload.js"
HARNESS="$ROOT/tests/component/g15_split_handle_customer_runtime.py"
OUT="${QA_OUT_DIR:-$(mktemp -d /tmp/logi-note-browser-logs.XXXXXX)}"
TMP="$(mktemp -d /tmp/logi-note-worktrees.XXXXXX)"
SERVER_PID=''
cleanup() {
  if [[ -n "$SERVER_PID" ]]; then kill "$SERVER_PID" 2>/dev/null || true; wait "$SERVER_PID" 2>/dev/null || true; fi
  "$CLI" close >/dev/null 2>&1 || true
  for name in PRE FIX; do
    if [[ -d "$TMP/$name" ]]; then git -C "$ROOT" worktree remove --force "$TMP/$name" >/dev/null 2>&1 || true; fi
  done
  rmdir "$TMP" 2>/dev/null || true
}
trap cleanup EXIT
if [[ -n "${MONGO_URI:-}" || "${ENV_IDENTITY:-PREVIEW}" == PRODUCTION ]]; then
  echo 'BLOCKED: real Mongo or production identity is forbidden' >&2; exit 2
fi
export MONGO_URI='' ENV_IDENTITY=PREVIEW AUTH_REQUIRED=false
export PLAYWRIGHT_CLI_SESSION="logi-note-regression-$$"
export PLAYWRIGHT_MCP_EXECUTABLE_PATH="$CHROME"
if [[ -d /tmp/al2023/lib ]]; then
  export LD_LIBRARY_PATH="/tmp/al2023/lib:/tmp${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
fi
if [[ ! -x "$CLI" || ! -x "$CHROME" || ! -f "$HARNESS" || ! -f "$FLOW" ]]; then
  echo 'BLOCKED: missing CLI/Chromium or QA assets' >&2; exit 2
fi
"$PY" -c 'import streamlit, mongomock' || { echo 'BLOCKED: missing Python QA dependencies' >&2; exit 2; }
mkdir -p "$OUT"
for sha in "$PRE" "$FIX"; do
  if ! git -C "$ROOT" cat-file -e "$sha^{commit}" 2>/dev/null; then git -C "$ROOT" fetch --no-tags origin "$sha"; fi
  git -C "$ROOT" cat-file -e "$sha^{commit}"
done
git -C "$ROOT" worktree add --detach "$TMP/PRE" "$PRE" >/dev/null
git -C "$ROOT" worktree add --detach "$TMP/FIX" "$FIX" >/dev/null
CASE_RC=90
run_one() {
  local name="$1" sha="$2"
  if [[ "$(git -C "$TMP/$name" rev-parse HEAD)" != "$sha" ]]; then CASE_RC=90; return; fi
  APP_ROOT="$TMP/$name" "$PY" -m streamlit run "$HARNESS" \
    --server.port=9502 --server.address=127.0.0.1 --server.headless=true >"$OUT/$name.app.log" 2>&1 &
  SERVER_PID=$!
  local ready=0
  for ((i=0;i<100;i++)); do
    if curl -fsS http://127.0.0.1:9502/_stcore/health >/dev/null 2>&1; then ready=1; break; fi
    sleep 0.25
  done
  if [[ "$ready" != 1 ]]; then
    CASE_RC=90; kill "$SERVER_PID" 2>/dev/null || true; wait "$SERVER_PID" 2>/dev/null || true; SERVER_PID=''; return
  fi
  if ! "$CLI" open http://127.0.0.1:9502/ >"$OUT/$name.open.log" 2>&1; then
    CASE_RC=90; kill "$SERVER_PID" 2>/dev/null || true; wait "$SERVER_PID" 2>/dev/null || true; SERVER_PID=''; return
  fi
  CASE_RC=0
  "$CLI" run-code --filename="$FLOW" >"$OUT/$name.browser.log" 2>&1 || CASE_RC=$?
  "$CLI" close >/dev/null 2>&1 || true
  kill "$SERVER_PID" 2>/dev/null || true; wait "$SERVER_PID" 2>/dev/null || true; SERVER_PID=''
  echo "$name exit=$CASE_RC sha=$sha"
}
run_one PRE "$PRE"; PRE_RC="$CASE_RC"
run_one FIX "$FIX"; FIX_RC="$CASE_RC"
if [[ "$PRE_RC" != 0 && "$PRE_RC" != 90 && "$FIX_RC" == 0 ]] \
   && grep -q JOURNEY_NOTE_DB_UNAVAILABLE "$OUT/PRE.app.log" \
   && grep -q QA_GATE_PASS "$OUT/FIX.browser.log"; then
  echo 'VERDICT=PROVEN PRE=FAIL FIX=PASS'
  echo "EVIDENCE=$OUT"
else
  echo "VERDICT=INCOMPLETE PRE_EXIT=$PRE_RC FIX_EXIT=$FIX_RC" >&2
  echo "EVIDENCE=$OUT" >&2
  exit 1
fi
