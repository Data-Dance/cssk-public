# Extension Plan — CZ/SK localization split + interactive docs

Target: split `sale_order_advance_invoice` into a country-neutral base + `l10n_cz_*` / `l10n_sk_*`
localizations (mirroring the Method A stock-valuation modules), and add Method A-style
Docutils documentation.

Decisions (locked):
1. Base stays `sale_order_advance_invoice`; add `l10n_cz_sale_order_advance_invoice` +
   `l10n_sk_sale_order_advance_invoice`.
2. Ship a **reconcilable clearing sub-account** per country; net advance liability uses chart 324000.
3. Docs = **Docutils RST→HTML** (navigable TOC + journal-entry tables), served as Apps description.
4. **Include long-term (475)** received-advance handling.

---

## Account mapping (verified against installed l10n_cz / l10n_sk charts)

| Company field (role) | reconcile | CZ code | SK code |
|---|---|---|---|
| `advance_received_account_id` — payment↔tax-doc **clearing/transit** | **True** (shipped sub-account) | `324001` *(new)* | `324001` *(new)* |
| `advance_tax_doc_account_id` — **short-term** net advance liability (tax-doc base + deduction) | False | `324000` (Přijaté provozní zálohy) | `324000` (Prijaté preddavky) |
| `advance_tax_doc_account_lt_id` — **long-term** net advance liability | False | `475000` (Dlouhodobé přijaté zálohy) | `475000` (Dlhodobé prijaté preddavky) |
| VAT | — | `343xxx` (chart) | `343xxx` (chart) |

Worked entry (short-term, VAT payer):
- Payment received:  **Dr 221 / Cr 324001**
- Tax document (daňový doklad k přijaté platbě / faktúra k prijatej platbe):
  **Dr 324001 / Cr 324000 (net) + Cr 343 (VAT)**  → reconcile the two 324001 legs (nets to 0)
- Final invoice: full revenue + full VAT, then settlement deduction **Dr 324000 / Cr 311** and
  reversal of the advance VAT already declared.

Long-term: same, with the net liability on **475000** instead of 324000, routed by a per-advance
`advance_invoice_long_term` flag.

---

## A. Base refactor — `sale_order_advance_invoice` → 19.0.2.0.0

- `tools.py`: `apply_advance_invoice_spec(env, chart_template_code, spec)` — resolve account *codes*
  to records per company on that chart_template, write company fields. Idempotent;
  **writes only when the field is empty** (don't clobber hand-configured deployments).
- `res_company.py`: `_resolve_advance_account(code)` + `_apply_advance_invoice_setup(spec)`;
  add `advance_tax_doc_account_lt_id`. Fix the multi-company journal bug (company-aware default,
  not `required` with a cross-company `env.ref`). Reconcile the journal type/domain mismatch.
- `sale_order.py`: add `advance_invoice_long_term` flag + route net liability to LT account;
  make the 15-day tax-doc deadline an overridable hook (`_advance_invoice_tax_doc_deadline`).
- Genericize CZ-flavoured help text (drop "e.g. 324000/324001" from base).
- Keep flags `is_advance_invoice` / `is_advance_invoice_tax_document` / `is_advance_tracking` /
  `advance_source_order_id` on the base (ISDOC bridge contract — unchanged).
- Housekeeping: author → Data Dance; `CHANGELOG.md`; regenerate `.pot`; fix drifted strings
  ("Invoice" → "Tax Document"); remove dead commented code; scaffold `tests/`.
- Docs: `docs/advance_invoice_cheat_sheet.rst` → `static/description/{index,advance_invoice_cheat_sheet}.html`.

## B. `l10n_cz_sale_order_advance_invoice`

- `depends = ['sale_order_advance_invoice', 'l10n_cz']`, `post_init_hook`, `auto_install = False`.
- `__init__.py`: `CZ_SPEC` (codes above) + hook → `apply_advance_invoice_spec(env, 'cz', CZ_SPEC)`.
- `data/account_account.xml`: ship reconcilable clearing `324001`; journal naming; sequence prefix.
- `static/description/index.html`: CZ accounts table, DUZP, daňový doklad k přijaté platbě, flow.
- `i18n/cs.po`: CZ-specific strings. Tests for the post_init mapping.

## C. `l10n_sk_sale_order_advance_invoice`

- `depends = ['sale_order_advance_invoice', 'l10n_sk']`; `SK_SPEC`; SK clearing `324001`.
- `static/description/index.html`: SK terms (preddavková faktúra / faktúra k prijatej platbe).
- `i18n/sk.po`. Tests.

---

## Gaps fixed along the way
1. Multi-company journal default crash. 2. Journal type/domain inconsistency. 3. Empty account
defaults (now set by l10n). 4. Hardcoded 15-day rule → hook. 5. No tests / author=Custom / stale .pot
/ dead code.

## Migration note
Existing deployments (two customers and the demo) configured the 3 accounts by hand. After
the split they install the matching l10n module; post_init fills only *empty* fields, so existing
config is preserved. ISDOC bridge unaffected (flags stay on base).

## Build order
1. Base refactor (tools + company + LT + bug fixes + docs scaffold).
2. l10n_cz (spec, accounts, docs, i18n, tests).
3. l10n_sk (spec, accounts, docs, i18n, tests).
4. Render Docutils HTML; verify install on a CZ and an SK company.
