# LOG-TRADE01 focused benchmark ledger

This tranche has no performance target and introduces no service/database. Record only bounded validation timing and result for the affected pure-Python module.

| Batch | Scope | Command | Result |
|---|---|---|---|
| B1 | Contract, source registry, identity, evidence, HS | `py -X utf8 -m unittest tests.test_log_trade01_trade_compliance -v` | PASS — 16 tests, 0.029s latest run |
| B2 | Regulatory, tariff, tax trace | same focused unittest module | PASS — included in 16-test run |
| B3 | Affected-module compile | in-memory `compile()` over 9 Python files | PASS — 9/9; `compileall` bytecode replacement separately blocked by WinError 5 |
| B4 | Diff hygiene | `git diff --check` | PASS — latest working-tree diff clean |
