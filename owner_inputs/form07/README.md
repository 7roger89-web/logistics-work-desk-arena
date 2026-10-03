# FORM_07 Owner source handoff

ISSUE=168
SOURCE_STATUS=VERIFIED_EXACT_BINARY
SOURCE_FILENAME=Mau-Bien-ban-giao-nhan-hang-hoa.docx
SOURCE_REPOSITORY_PATH=owner_inputs/form07/Mau-Bien-ban-giao-nhan-hang-hoa.docx
SOURCE_SIZE_BYTES=18997
SOURCE_SHA256=cd2a1df5434a217bdae34e292844ad1bacbcc737b2282137b835af46663161b5
SOURCE_GIT_BLOB_SHA=e2c3dea169bff006f4073f7fae2b2c285c912f3f
SOURCE_LOCAL_VALIDATION=OOXML_ZIP_VALID
SOURCE_HAS_VBA=NO
SOURCE_HAS_COMMENTS_PART=NO
SOURCE_HAS_EXTERNAL_LINKS_PART=NO
SOURCE_HAS_EMBEDDINGS=NO
SOURCE_HAS_ACTIVEX=NO

This branch is an Owner-input transport branch only.

Control Tower independently fetched the repository file as base64 and recomputed:

- byte length: 18997
- SHA-256: cd2a1df5434a217bdae34e292844ad1bacbcc737b2282137b835af46663161b5

These exactly match the Owner-uploaded source observed by Control Tower.

Writer/Arena must still verify the file itself before use:

```bash
sha256sum owner_inputs/form07/Mau-Bien-ban-giao-nhan-hang-hoa.docx
```

Expected:

```
cd2a1df5434a217bdae34e292844ad1bacbcc737b2282137b835af46663161b5
```

Do NOT merge this transport branch to main.

The Writer should start from fresh current `main`, fetch/copy this exact source from
`owner-input/form07-source-168` for inspection/sanitization, and commit only the
derived production-safe template/spec required by Issue #168.

The original is evidence/input, not a production template and not authority to create new business rules.
