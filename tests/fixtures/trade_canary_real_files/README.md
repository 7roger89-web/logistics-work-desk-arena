# Trade canary Run 2 real-file fixtures

These files are synthetic test fixtures for issue #130. They are not customer or shipment records.

Files:

- `commercial_invoice.xlsx`
- `packing_list.xlsx`
- `bill_of_lading.pdf`

Every visible XLSX sheet and every PDF page contains:

`SYNTHETIC — NOT A REAL SHIPMENT`

Fixture provenance:

- The XLSX files are minimal Office Open XML workbooks generated with Python standard-library `zipfile` and inline string cells. No macros are present and no formulas are required for the golden fixtures.
- The PDF is a tiny hand-written born-digital PDF using a standard Helvetica font and text content streams. It was not generated with ReportLab/fpdf and it has no images/OCR layer.
- The business values intentionally match Run 1 `tests/fixtures/trade_canary/*.txt` so the same 19 semantic facts can be checked through real file bytes.

Current SHA-256 values:

- `commercial_invoice.xlsx`: `679bd628b09a859f9dbedca1d5ee60089f78493ac9a052b6bf9c7810802dbfcb`
- `packing_list.xlsx`: `3a179be0f5058bfe8ea4aa9a7ceab176f23db96af6dcd23643d0afa2344691b2`
- `bill_of_lading.pdf`: `31e75fdbb755fd3b6991999085c409ed53ffe38f268368c4c2dc8a97f3f72e98`
