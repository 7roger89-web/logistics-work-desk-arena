#!/usr/bin/env bash
# LOGI-247-STAGING-READBACK-20261031 — read-only staging readback collector.
# Re-records every measurement used in the readback verdict into transcript.txt.
# It never merges, never pushes, never writes any branch or PR.
set -u
REPO=7roger89-web/logistics-work-desk-arena
PR=248
ACC=9012ee01763df491ec4d8bda9836cc3dee060aac
STG=arena/ae5f9f47-logistics-work-desk-arena
S1=3516ce702f90d5a4a8582702ab0f9e38a1bd8cc6
OUT="$(dirname "$0")/transcript.txt"
T=/tmp/rb-tmp; mkdir -p "$T"

say() { echo; echo "########## $* ##########"; }

: > "$OUT"
exec >> "$OUT" 2>&1

say "A. PR #248 state and merge"
echo "\$ gh api repos/$REPO/pulls/$PR --jq '{number,state,merged,merged_at,merge_commit_sha,head:.head.sha,base:.base.ref,draft,mergeable,mergeable_state}'"
gh api "repos/$REPO/pulls/$PR" --jq '{number,state,merged,merged_at,merge_commit_sha,head:.head.sha,base:.base.ref,draft,mergeable,mergeable_state}'; echo "EXIT=$?"
echo
echo "\$ gh api repos/$REPO/pulls/$PR/merge --jq '.merged'   # 404/exit 1 => never merged"
gh api "repos/$REPO/pulls/$PR/merge" --jq '.merged'; echo "EXIT=$?"
echo
echo "\$ gh pr checks $PR"
gh pr checks "$PR"; echo "EXIT=$?"

say "B. Branch inventory — is there a 'staging' ref at all?"
echo "\$ gh api repos/$REPO/branches --paginate --jq '.[].name' > /tmp/rb_branches.txt"
gh api "repos/$REPO/branches" --paginate --jq '.[].name' > /tmp/rb_branches.txt; echo "EXIT=$?"
echo "BRANCH_TOTAL=$(wc -l < /tmp/rb_branches.txt)"
echo
echo "\$ grep -iE 'staging|stage|preprod|uat' /tmp/rb_branches.txt"
grep -iE "staging|stage|preprod|uat" /tmp/rb_branches.txt; echo "GREP_EXIT=$? (1 = no staging-named branch exists)"
echo
echo "\$ gh api repos/$REPO/branches/staging --jq '.name'"
gh api "repos/$REPO/branches/staging" --jq '.name'; echo "EXIT=$?"
echo
echo "\$ gh api repos/$REPO/branches/$STG --jq '{name,sha:.commit.sha}'   # declared staging candidate"
gh api "repos/$REPO/branches/$STG" --jq '{name,sha:.commit.sha}'; echo "EXIT=$?"

say "C. Ancestry — does staging contain the accepted head?"
echo "\$ gh api repos/$REPO/commits/$ACC --jq '{sha,parents:[.parents[].sha],date:.commit.author.date,message:(.commit.message|split(\"\\n\")[0])}'"
gh api "repos/$REPO/commits/$ACC" --jq '{sha,parents:[.parents[].sha],date:.commit.author.date,message:(.commit.message|split("\n")[0])}'; echo "EXIT=$?"
echo
echo "\$ gh api repos/$REPO/compare/$STG...$ACC   # ahead_by>0 / behind_by=0 => staging LACKS the work"
gh api "repos/$REPO/compare/$STG...$ACC" --jq '{merge_base:.merge_base_commit.sha,status,ahead_by,behind_by,commits:[.commits[]|"\(.sha[0:7]) \(.commit.message|split("\n")[0])"]}'; echo "EXIT=$?"
echo
echo "\$ gh api repos/$REPO/compare/main...$ACC"
gh api "repos/$REPO/compare/main...$ACC" --jq '{status,ahead_by,behind_by}'; echo "EXIT=$?"
echo
echo "\$ gh api repos/$REPO/compare/$STG...1540a04 --jq '{status,ahead_by}'   # merge_commit_sha field of the OPEN pr = ephemeral test-merge"
gh api "repos/$REPO/compare/$STG...1540a04e1060933d184feb174fd42c0c100aa5ce" --jq '{status,ahead_by}'; echo "EXIT=$?"

say "D. S1/S2/S3 blob integrity across refs (sha256 of file contents)"
for ref in "$ACC" "$S1" "$STG" main; do
  for p in tests/test_intl_payment_comparator.py core/database.py \
           playwright/issue247_s2_browser.mjs playwright/issue247_s3_browser.mjs \
           tests/component/g15_lg_tt_discussion_runtime.py; do
    f="$T/$(echo "$ref" | tr '/' '_')_$(basename "$p")"
    echo "\$ sha256 $p @ $ref"
    gh api "repos/$REPO/contents/$p?ref=$ref" --jq '.content' > "$f.b64"; rc=$?
    if [ "$rc" -eq 0 ] && [ -s "$f.b64" ] && base64 -d "$f.b64" > "$f" 2>/dev/null && [ -s "$f" ]; then
      sha256sum "$f" | sed "s#  $f#  <$p @ $ref>#"
    else
      echo "MISSING_AT_THIS_REF (404)"
    fi
    echo "EXIT=$rc"
  done
done

say "E. S1 additions present at accepted head but absent in staging"
echo "\$ diff -u <staging:tests/test_intl_payment_comparator.py> <accepted:tests/test_intl_payment_comparator.py> | grep -E '^\\+def test_'"
diff -u "$T/arena_ae5f9f47-logistics-work-desk-arena_test_intl_payment_comparator.py" \
        "$T/${ACC}_test_intl_payment_comparator.py" | grep -E "^\+def test_"; echo "GREP_EXIT=$?"
echo
echo "\$ cmp <3516ce7>core/database.py <accepted>core/database.py   # S1 product source unchanged?"
cmp "$T/${S1}_database.py" "$T/${ACC}_database.py"; echo "CMP_EXIT=$?"

say "DONE"
echo "COLLECT_DONE"
