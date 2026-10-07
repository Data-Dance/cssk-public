# -*- coding: utf-8 -*-
"""Move Slovak partners off 9950 (IČ DPH) onto 0245 (DIČ).

``_compute_peppol_eas`` recomputes only when the stored value is not already a
valid code for the country, which is how a scheme somebody chose deliberately
survives an upgrade. The side effect is that every Slovak partner already
carrying ``9950`` keeps it — and almost all of them carry it because core
*defaulted* them there, not because anyone chose it.

The work itself lives in ``res.partner.action_l10n_sk_adopt_dic_participant``
rather than here, because this migration cannot be the only way to run it. It
fires at upgrade, which is *before* anyone has had the chance to record the DIČs
it requires, so on a fresh upgrade it legitimately skips almost everything. The
DIČs get recorded afterwards — ``partner_autocomplete_orsf_sk`` has
``action_orsf_fill_missing_dic`` for that — and at that point the move has to be
runnable again. One implementation, two callers.
"""

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    from odoo import api, SUPERUSER_ID

    env = api.Environment(cr, SUPERUSER_ID, {})
    Partner = env["res.partner"]
    if "l10n_sk_dic" not in Partner._fields:
        _logger.warning(
            "l10n_sk_ubl_bis3: l10n_sk_base is not installed; leaving "
            "peppol_eas alone."
        )
        return

    candidates = Partner.with_context(active_test=False).search(
        [("peppol_eas", "!=", "0245"), ("country_id.code", "=", "SK")]
    )
    moved = candidates.action_l10n_sk_adopt_dic_participant()
    _logger.info(
        "l10n_sk_ubl_bis3: upgrade moved %s of %s Slovak partner(s) onto "
        "0245. Any left behind are waiting on a DIČ — record them "
        "(partner_autocomplete_orsf_sk: 'Fill missing DIČ') and re-run "
        "action_l10n_sk_adopt_dic_participant; this migration will not fire "
        "again.",
        len(moved), len(candidates),
    )
