#!/usr/bin/env bash
# OPS-SOURCE-RETRIEVAL-FIX-20261101 — kiểm chứng nguồn đọc Control Tower.
# Phần LIVE: đọc thật từ GitHub bằng gh api và git show origin/main, so khớp nội dung.
# Phần SIM: ma trận quyết định theo luật trong 00-LUAT.md (mô phỏng, KHÔNG phải chạy ChatGPT thật).
# Không ghi gì ngoài thư mục evidence của task này.
set -u
REPO="7roger89-web/logistics-work-desk-arena"
FILES=(ops/arena-control/00-LUAT.md ops/arena-control/05-TRANG-THAI.md ops/arena-control/06-NHAT-KY.md)
EV="evidence/OPS-SOURCE-RETRIEVAL-FIX-20261101"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
FAILS=0
ok()   { echo "PASS  $*"; }
bad()  { echo "FAIL  $*"; FAILS=$((FAILS+1)); }

echo "== LIVE: nguồn GitHub thật"
MAIN_API="$(gh api "repos/$REPO/commits/main" --jq .sha 2>/dev/null)"; echo "gh commits/main sha=$MAIN_API"
git fetch --quiet origin main 2>/dev/null; ORIGIN="$(git rev-parse origin/main)"; echo "origin/main sha=$ORIGIN"
[ -n "$MAIN_API" ] && [ "$MAIN_API" = "$ORIGIN" ] && ok "READ_REF verified: origin/main == gh main" || bad "READ_REF mismatch"
READ_REF="$ORIGIN"

READ_FILES=()
GH_ALL_OK=1
for f in "${FILES[@]}"; do
  gh api "repos/$REPO/contents/$f?ref=main" --jq .content 2>/dev/null | base64 -d > "$TMP/gh.$(basename "$f")"
  gh_rc=${PIPESTATUS[0]}
  git show "origin/main:$f" > "$TMP/git.$(basename "$f")" 2>/dev/null; git_rc=$?
  gs="$(sha256sum "$TMP/gh.$(basename "$f")" | cut -c1-64)"
  gi="$(sha256sum "$TMP/git.$(basename "$f")" | cut -c1-64)"
  echo "$f gh_rc=$gh_rc git_rc=$git_rc gh_sha256=$gs git_sha256=$gi bytes=$(wc -c < "$TMP/git.$(basename "$f")")"
  if [ "$gh_rc" = 0 ] && [ "$git_rc" = 0 ] && [ -s "$TMP/git.$(basename "$f")" ] && [ "$gs" = "$gi" ]; then
    ok "content match gh<->git: $f"; READ_FILES+=("$f")
  else
    [ "$gh_rc" = 0 ] || GH_ALL_OK=0
    bad "content mismatch or read failure: $f"
  fi
done

# STATE_PREFIX: 6 ký tự đầu (theo ký tự Unicode) của 05, lấy động
STATE_PREFIX="$(python3 -c 'import sys;print(open(sys.argv[1],encoding="utf-8").read()[:6])' "$TMP/git.05-TRANG-THAI.md")"
echo "STATE_PREFIX(dynamic)=[$STATE_PREFIX]"
[ "$(python3 -c 'import sys;print(len(sys.argv[1]))' "$STATE_PREFIX")" = 6 ] && ok "STATE_PREFIX computed dynamically (6 Unicode chars)" || bad "STATE_PREFIX length"

echo "== LIVE: phân loại lỗi thật (negative)"
gh api "repos/$REPO/contents/ops/arena-control/NOPE-404.md?ref=main" >/dev/null 2>"$TMP/e404"; rc404=$?
grep -q "404" "$TMP/e404" && ok "missing file on readable repo => NOT_FOUND (HTTP 404, rc=$rc404)" || bad "expected 404 classification"
git show "origin/main:ops/arena-control/NOPE-404.md" >/dev/null 2>&1; rcgit=$?
[ "$rcgit" != 0 ] && ok "git show missing path fails (rc=$rcgit) => NOT_FOUND" || bad "git show missing path should fail"
curl -sS -m 20 -o /dev/null "https://raw.githubusercontent.com/$REPO/main/ops/arena-control/05-TRANG-THAI.md" 2>/dev/null; rcraw=$?
echo "raw.githubusercontent.com curl_rc=$rcraw"
[ "$rcraw" != 0 ] && ok "raw host failing (rc=$rcraw) classified NETWORK_FAILURE, not NOT_FOUND" || echo "INFO  raw host reachable now (rc=0)"

echo "== SIM: ma trận quyết định theo 00-LUAT (không phải chạy ChatGPT thật)"
# decide <connector_ok> <gh_ok> <git_ok> <url_ok>
decide() {
  if [ "$1" = 1 ]; then echo "GITHUB_CONNECTOR SUCCESS"
  elif [ "$2" = 1 ]; then echo "GH_API SUCCESS"
  elif [ "$3" = 1 ]; then echo "GIT_SHOW_ORIGIN_MAIN SUCCESS"
  elif [ "$4" = 1 ]; then echo "URL_FALLBACK SUCCESS"
  else echo "NONE BLOCKED"; fi
}
A="$(decide 1 0 0 0)"   # web fetch lỗi, connector đọc được
B="$(decide 0 1 0 0)"   # không connector, gh api đọc được
C="$(decide 0 0 0 0)"   # mọi nguồn lỗi
echo "A(connector ok, web fail)  => $A"
echo "B(no connector, gh ok)     => $B"
echo "C(all sources fail)        => $C"
[ "$A" = "GITHUB_CONNECTOR SUCCESS" ] && ok "Acceptance A (sim)" || bad "A"
[ "$B" = "GH_API SUCCESS" ] && ok "Acceptance B (sim)" || bad "B"
[ "$C" = "NONE BLOCKED" ] && ok "Acceptance C (sim)" || bad "C"

echo "== RECEIPT"
{
  echo "# SOURCE_RECEIPT — OPS-SOURCE-RETRIEVAL-FIX-20261101"
  if [ "$GH_ALL_OK" = 1 ]; then echo "READ_SOURCE=GH_API"
  elif [ "${#READ_FILES[@]}" = 3 ]; then echo "READ_SOURCE=GIT_SHOW_ORIGIN_MAIN"
  else echo "READ_SOURCE=NONE"; fi
  echo "READ_REF=$READ_REF"
  echo "READ_FILES=${READ_FILES[*]}"
  echo "STATE_PREFIX=$STATE_PREFIX"
  if [ "${#READ_FILES[@]}" = 3 ]; then echo "READ_STATUS=SUCCESS"; else echo "READ_STATUS=BLOCKED"; fi
  echo "NOTE=GitHub connector không có trong Arena (list_connector_tools=unsupported). Kịch bản A chỉ mô phỏng."
} | tee "$EV/SOURCE_RECEIPT.md"

echo "== RESULT: fails=$FAILS"
[ "$FAILS" = 0 ]
