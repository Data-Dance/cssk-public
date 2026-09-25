# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': "AI Invoice Extraction (vyťažovanie faktúr)",
    'summary': "Read supplier invoice PDFs with an LLM and create draft vendor bills",
    'description': """
AI Invoice Extraction
=====================

Autonomous accounts-payable pipeline built on ``muk_ai``:

- Ingest supplier invoice PDFs (vendor-bill email alias or manual upload).
- The model extracts **natural keys only** (supplier VAT, ISO currency, dates,
  amounts, per-rate VAT breakdown, reverse-charge hint) via a forced tool call.
- A **deterministic Python resolver** maps that data to Odoo records: supplier by
  VAT, domestic VAT rate → tax, fiscal position drives the reverse-charge /
  intra-EU remap, duplicate detection, sanity gates.
- Always creates a **DRAFT** ``account.move``; the source PDF and the raw model
  JSON are kept for audit, with per-run token counts and cost.

The split matters: the model is never asked to pick an Odoo record. It returns
keys a human could verify from the page, and Python resolves them. That is what
keeps a wrong answer visible instead of silently mis-posted.

This is the *vyťažovanie došlých faktúr* component of the CZ/SK localization, and
the Community answer to Odoo Enterprise's IAP-based ``account_invoice_extract``.
It is country-neutral — the SK/CZ specifics live in the fiscal positions and the
VAT-rate → tax map, not here.
""",
    'version': '19.0.1.0.0',
    'category': 'Accounting',
    'license': "AGPL-3",
    'author': "Data Dance s.r.o.",
    'website': "https://www.datadance.eu",
    'depends': [
        'account',
        'muk_ai',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'data/ir_cron.xml',
        'views/ai_extraction_views.xml',
        'views/account_move_views.xml',
        'views/res_config_settings_views.xml',
        'views/menu.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
}
