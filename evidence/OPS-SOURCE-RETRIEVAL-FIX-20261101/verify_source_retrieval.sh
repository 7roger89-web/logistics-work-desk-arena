#!/usr/bin/env bash
# OPS-SOURCE-RETRIEVAL-FIX-20261101 — kiểm chứng nguồn đọc Control Tower (v2).
# Nhãn: LIVE = gọi mạng thật trong lần chạy này; SIM = dùng body thật đã lưu, không phải ChatGPT thật.
# Cổng nội dung: source_gate.py. Không ghi ngoài thư mục evidence của task.
set -u
REPO="7roger89-web/logistics-work-desk-arena"
EV="evidence/OPS-SOURCE-RETRIEVAL-FIX-20261101"
GATE="python3 $EV/source_gate.py"
FILES=(ops/arena-control/00-LUAT.md ops/arena-control/05-TRANG-THAI.md ops/arena-control/06-NHAT-KY.md)
declare -A HDR=(
  [ops/arena-control/00-LUAT.md]="# LUẬT CONTROL TOWER"
  [ops/arena-control/05-TRANG-THAI.md]="# TRẠNG THÁI"
  [ops/arena-control/06-NHAT-KY.md]="# NHẬT KÝ (chỉ nối thêm, không sửa dòng cũ)"
)
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
RAW_DIR="$EV/raw/v2"; mkdir -p "$RAW_DIR"
FAILS=0
ok()  { echo "PASS  $*"; }
bad() { echo "FAIL  $*"; FAILS=$((FAILS+1)); }
expect() { # expect <label> <got> <want-prefix>
  if [[ "$2" == "$3"* ]]; then ok "$1 -> $2"; else bad "$1 -> got '$2' want '$3'"; fi
}

echo "== REF"
git fetch -q origin main 2>/dev/null
ORIGIN="$(git rev-parse origin/main)"
GH_MAIN="$(gh api "repos/$REPO/commits/main" --jq .sha 2>/dev/null)"
echo "origin/main=$ORIGIN gh_main=$GH_MAIN"
[ "$ORIGIN" = "$GH_MAIN" ] && ok "READ_REF: origin/main == gh main" || bad "READ_REF mismatch"
READ_REF="$ORIGIN"

echo "== LIVE: từng tầng trên 3 file"
declare -A V_GH V_GIT V_API V_RAW V_BLOB EXP
READ_OK=()
for f in "${FILES[@]}"; do
  b="$(basename "$f")"; h="${HDR[$f]}"
  git show "origin/main:$f" > "$TMP/$b.git"; grc=$?
  EXP[$b]="$(sha256sum "$TMP/$b.git" | cut -c1-64)"
  # gh api (contents JSON, ref=main)
  gh api "repos/$REPO/contents/$f?ref=main" > "$TMP/$b.gh.json" 2>"$TMP/$b.gh.err"; grc2=$?
  if [ $grc2 = 0 ]; then st=200; elif grep -q "HTTP 404" "$TMP/$b.gh.err"; then st=404; else st=0; fi
  gcrc=0; [ $st = 0 ] && gcrc=1
  V_GH[$b]="$($GATE --kind contents_json --status $st --curl-rc $gcrc --body "$TMP/$b.gh.json" --path "$f" --header "$h" --expect-sha256 "${EXP[$b]}")"
  # git show (raw text, ref-verified)
  V_GIT[$b]="$($GATE --kind raw_text --status 200 --curl-rc $grc --body "$TMP/$b.git" --path "$f" --header "$h" --expect-sha256 "${EXP[$b]}")"
  # api.github.com contents (URL fallback tầng 2)
  : > "$RAW_DIR/api-$b.json"
  curl -sS -m 30 -o "$RAW_DIR/api-$b.json" -w "%{http_code}" "https://api.github.com/repos/$REPO/contents/$f?ref=main" > "$TMP/st" 2>"$TMP/curl.err"; crc=$?
  V_API[$b]="$($GATE --kind contents_json --status "$(cat $TMP/st)" --curl-rc $crc --body "$RAW_DIR/api-$b.json" --path "$f" --header "$h" --expect-sha256 "${EXP[$b]}")"
  # raw.githubusercontent (URL fallback tầng 1)
  : > "$RAW_DIR/raw-$b.body"
  curl -sS -m 30 -o "$RAW_DIR/raw-$b.body" -w "%{http_code}" "https://raw.githubusercontent.com/$REPO/main/$f" > "$TMP/st" 2>"$TMP/curl.err"; crc=$?
  V_RAW[$b]="$($GATE --kind raw_text --status "$(cat $TMP/st)" --curl-rc $crc --body "$RAW_DIR/raw-$b.body" --path "$f" --header "$h" --expect-sha256 "${EXP[$b]}")"
  # github.com/blob — KHÔNG nằm trong fallback; chỉ kiểm chứng rằng HTTP 200 HTML bị chặn
  : > "$RAW_DIR/blob-$b.html"
  curl -sS -m 30 -o "$RAW_DIR/blob-$b.html" -w "%{http_code}" "https://github.com/$REPO/blob/main/$f" > "$TMP/st" 2>"$TMP/curl.err"; crc=$?
  V_BLOB[$b]="$($GATE --kind raw_text --status "$(cat $TMP/st)" --curl-rc $crc --body "$RAW_DIR/blob-$b.html" --path "$f" --header "$h" --expect-sha256 "${EXP[$b]}")"
  echo "--- $f"
  echo "gh_api : ${V_GH[$b]}"; echo "git    : ${V_GIT[$b]}"; echo "api_url: ${V_API[$b]}"
  echo "raw_url: ${V_RAW[$b]}"; echo "blob   : ${V_BLOB[$b]}"
  expect "LIVE gh_api $b" "${V_GH[$b]%% *}" "SUCCESS"
  expect "LIVE git $b" "${V_GIT[$b]%% *}" "SUCCESS"
  expect "LIVE api_url $b (decode base64)" "${V_API[$b]%% *}" "SUCCESS"
  expect "LIVE raw_url $b (mạng sandbox)" "${V_RAW[$b]%% *}" "NETWORK_FAILURE"
  expect "LIVE blob HTML bị chặn $b" "${V_BLOB[$b]%% *}" "HTML_PAGE"
  [ "${V_GH[$b]%% *}" = SUCCESS ] && READ_OK+=("$f")
done

echo "== LIVE: sai ref (file 05 ở commit cũ hơn) phải bị WRONG_REF"
CUR_BLOB="$(gh api "repos/$REPO/contents/ops/arena-control/05-TRANG-THAI.md?ref=main" --jq .sha 2>/dev/null)"
OLD=""
for c in $(gh api "repos/$REPO/commits?path=ops/arena-control/05-TRANG-THAI.md&sha=main&per_page=20" --jq '.[].sha' 2>/dev/null); do
  b="$(gh api "repos/$REPO/contents/ops/arena-control/05-TRANG-THAI.md?ref=$c" --jq .sha 2>/dev/null)"
  if [ -n "$b" ] && [ "$b" != "$CUR_BLOB" ]; then OLD="$c"; break; fi
done
echo "older_ref_with_different_05=$OLD cur_blob=$CUR_BLOB"
gh api "repos/$REPO/contents/ops/arena-control/05-TRANG-THAI.md?ref=$OLD" > "$TMP/old.json" 2>/dev/null; orc=$?
[ -f "$TMP/old.json" ] || : > "$TMP/old.json"
v="$($GATE --kind contents_json --status $([ $orc = 0 ] && echo 200 || echo 404) --curl-rc 0 --body "$TMP/old.json" --path ops/arena-control/05-TRANG-THAI.md --header "${HDR[ops/arena-control/05-TRANG-THAI.md]}" --expect-sha256 "${EXP[05-TRANG-THAI.md]}")"
echo "old_ref=$OLD verdict: $v"; expect "LIVE wrong ref 05@$OLD" "${v%% *}" "WRONG_REF"

echo "== LIVE: file không tồn tại (NOT_FOUND)"
gh api "repos/$REPO/contents/ops/arena-control/NOPE-404.md?ref=main" > "$TMP/nf.json" 2>"$TMP/nf.err"; nrc=$?
st=0; grep -q "HTTP 404" "$TMP/nf.err" && st=404
ncrc=0; [ $st = 0 ] && ncrc=1
v="$($GATE --kind contents_json --status $st --curl-rc $ncrc --body "$TMP/nf.json" --path x --header x)"
echo "verdict: $v"; expect "LIVE NOT_FOUND" "${v%% *}" "NOT_FOUND"

echo "== SIM: chặn CACHE_MISS và JSON/rỗng/sai header (body giả lập, nhãn SIM)"
printf 'Cache miss for this URL' > "$TMP/cm.txt"
v="$($GATE --kind raw_text --status 200 --body "$TMP/cm.txt" --path p --header h)"; echo "SIM cache-miss: $v"; expect "SIM CACHE_MISS" "${v%% *}" "CACHE_MISS"
: > "$TMP/empty.txt"
v="$($GATE --kind raw_text --status 200 --body "$TMP/empty.txt" --path p --header h)"; echo "SIM empty: $v"; expect "SIM EMPTY" "${v%% *}" "EMPTY"
printf '# SAI TIEU DE\nabc\n' > "$TMP/wh.txt"
v="$($GATE --kind raw_text --status 200 --body "$TMP/wh.txt" --path p --header "# TRẠNG THÁI")"; echo "SIM wrong header: $v"; expect "SIM HEADER_MISMATCH" "${v%% *}" "HEADER_MISMATCH"
printf '{"content":"IyBhYg==","encoding":"base64"}' > "$TMP/j.json"
v="$($GATE --kind contents_json --status 200 --body "$TMP/j.json" --path p --header h)"; echo "SIM json no path: $v"; expect "SIM WRONG_PATH" "${v%% *}" "WRONG_PATH"
printf '{"content":"!!!","encoding":"base64","path":"p"}' > "$TMP/j2.json"
v="$($GATE --kind contents_json --status 200 --body "$TMP/j2.json" --path p --header h)"; echo "SIM bad base64: $v"; expect "SIM base64 invalid" "${v%% *}" "ENCODING_INVALID"
printf 'not json' > "$TMP/j3.json"
v="$($GATE --kind contents_json --status 200 --body "$TMP/j3.json" --path p --header h)"; echo "SIM json invalid: $v"; expect "SIM JSON_INVALID" "${v%% *}" "JSON_INVALID"

echo "== SIM: ma trận lựa chọn nguồn (kết quả cổng thật, theo thứ tự connector > gh > git > raw > api)"
# choose <connector> <gh> <git> <raw> <api>  (mỗi tham số là verdict của cổng)
choose() {
  local names=(GITHUB_CONNECTOR GH_API GIT_SHOW_ORIGIN_MAIN URL_FALLBACK URL_FALLBACK) i
  local vs=("$@")
  for i in 0 1 2 3 4; do
    if [ "${vs[$i]}" = SUCCESS ]; then echo "${names[$i]} SUCCESS tried=$((i+1))"; return; fi
  done
  echo "NONE BLOCKED tried=5"
}
A="$(choose SUCCESS NO_ACCESS NO_ACCESS HTML_PAGE NO_ACCESS)"; echo "SIM-A connector OK, web HTML: $A"
expect "SIM-A" "$A" "GITHUB_CONNECTOR SUCCESS tried=1"
B="$(choose NO_ACCESS SUCCESS NO_ACCESS NETWORK_FAILURE SUCCESS)"; echo "SIM-B no connector, gh OK: $B"
expect "SIM-B" "$B" "GH_API SUCCESS tried=2"
C="$(choose NO_ACCESS NETWORK_FAILURE NO_ACCESS NETWORK_FAILURE HTML_PAGE)"; echo "SIM-C mọi nguồn lỗi: $C"
expect "SIM-C" "$C" "NONE BLOCKED tried=5"
D="$(choose NO_ACCESS NO_ACCESS NO_ACCESS NETWORK_FAILURE SUCCESS)"; echo "SIM-D chỉ api_url đọc được: $D"
expect "SIM-D" "$D" "URL_FALLBACK SUCCESS tried=5"

echo "== STATE_PREFIX (động từ 05 của origin/main)"
SP="$(python3 -c 'import sys;print(open(sys.argv[1],encoding="utf-8").read()[:6])' "$TMP/05-TRANG-THAI.md.git")"
echo "STATE_PREFIX=[$SP] len=$(python3 -c 'import sys;print(len(sys.argv[1]))' "$SP")"
expect "STATE_PREFIX len" "$(python3 -c 'import sys;print(len(sys.argv[1]))' "$SP")" "6"

if [ "${#READ_OK[@]}" = 3 ]; then RS=SUCCESS; elif [ "${#READ_OK[@]}" -ge 1 ]; then RS=PARTIAL; else RS=BLOCKED; fi
{
  echo "# SOURCE_RECEIPT — OPS-SOURCE-RETRIEVAL-FIX-20261101 (v2)"
  echo "READ_SOURCE=GH_API"
  echo "READ_REF=$READ_REF"
  echo "READ_FILES=${READ_OK[*]}"
  echo "STATE_PREFIX=$SP"
  echo "READ_STATUS=$RS"
  echo "NOTE=connector GitHub không có trong Arena (unsupported). Kịch bản connector và các kịch bản SIM ghi nhãn SIM."
} > "$EV/SOURCE_RECEIPT.md"
cat "$EV/SOURCE_RECEIPT.md"
echo "== RESULT fails=$FAILS"
[ "$FAILS" = 0 ]
