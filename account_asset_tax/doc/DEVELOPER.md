# account_asset_tax: developer notes

Not user documentation: this file is not rendered into a page.

## Engine

All statutory maths lives in `engine/depreciation.py` with **no Odoo import**,
so it is unit-tested in isolation (`tests/test_engine.py`, runnable with plain
`python3`) and reused unchanged by both bridges, which differ only in *where*
they read the entry value and in-service date.
