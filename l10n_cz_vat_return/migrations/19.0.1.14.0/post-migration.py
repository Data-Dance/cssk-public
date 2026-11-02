# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""ř. 47 — the asset-acquisition twins, for companies that already exist.

``l10n_cz`` declares ``VAT 47 Base`` and ``VAT 47 Total`` and ships no tax
carrying either, so *hodnota pořízeného majetku* filed 0.00 on every return
this module has ever produced. The twins are what give an accountant a way to
say "this purchase is a long-term asset"; see
``res_company._cz_create_asset_acquisition_taxes``.

Nothing already posted is touched. A twin is a NEW tax, so a bill booked
against the plain purchase tax keeps every tag it has and every figure it
reports, and ř. 47 stays empty for past periods.

⚠️ That is a DECISION, not an impossibility, and the first draft of this note
got it wrong by saying nothing in the database records which purchases were
assets. Something can: ``account_asset_management`` sets ``asset_id`` on the
BILL's own line at post time (``models/account_move.py``, in ``action_post``),
so wherever that module is in use the asset acquisitions are a recorded fact
and ř. 47 is derivable for history. Corrected after a Vario rehearsal
measured this release against filed returns: ř. 47 matched to the koruna in
9 of 11 periods from the tax position alone, and the two misses were vehicle
bills whose lines carry the plain domestic position and whose asset nature is
recorded only in the source system's asset register.

Still not done here, for reasons that are about this being a MIGRATION rather
than about the information being absent:

* the asset module is optional, and a migration must not depend on one;
* the link exists only for assets created THROUGH that flow — one entered by
  hand, or imported from a legacy register, has none — so the pass would be
  silently partial, which is the failure mode this module keeps finding;
* ``tax_tag_ids`` is lock-date protected, so writing it means going round the
  ORM in SQL (see 18.0's ``_cz_retag_posted_selfassessed_lines``);
* and re-tagging a filed period adds reporting to a return that was already
  filed. That is the taxpayer's call, not an upgrade's.

If it is wanted, it belongs in a reviewable wizard that shows the accountant
which documents it proposes to re-tag, not in an upgrade that runs unattended.
"""
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    companies = env["res.company"].search([("chart_template", "=", "cz")])
    if not companies:
        return
    companies._cz_create_asset_acquisition_taxes()
    # The twins did not exist when the historical rates were generated, so
    # generate them again — the pass adopts rather than duplicates.
    companies._cssk_create_historic_vat_taxes()
