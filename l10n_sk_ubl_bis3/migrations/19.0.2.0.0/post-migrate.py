# -*- coding: utf-8 -*-
"""Move Slovak partners off 9950 (IČ DPH) onto 0245 (DIČ).

``_compute_peppol_eas`` recomputes only when the stored value is not already a
valid code for the country, which is how a scheme somebody chose deliberately
survives an upgrade. The side effect is that every Slovak partner already
carrying ``9950`` keeps it — and almost all of them carry it because core
*defaulted* them there, not because anyone chose it. Leaving them would publish
the whole address book under the wrong scheme, which is the thing this release
exists to stop.

So the move is made here, once, explicitly, and only where it is safe:

* the partner must be Slovak;
* it must currently be on ``9950``;
* a DIČ must be RECORDED on the partner. It is deliberately not derived from
  the VAT number (see ``_l10n_sk_get_dic``), so on most databases this is the
  condition that skips rows, and the log is the list of contacts needing the
  DIČ entered before they can be e-invoiced. Flipping the scheme without a number to publish would leave the old
  IČ DPH sitting in ``peppol_endpoint`` labelled as a DIČ, because
  ``_compute_peppol_endpoint`` keeps the previous value when the new one is
  empty;
* and the endpoint it currently holds must be the one core derived from the VAT
  number. A partner whose endpoint was typed by hand is left alone: that is a
  deliberate registration, and a migration has no business overruling it.

Anything skipped is logged with its id, so the set that needs a human is a
grep rather than a guess.
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
        [("peppol_eas", "=", "9950"), ("country_id.code", "=", "SK")]
    )
    moved, skipped = Partner, []
    for partner in candidates:
        dic = partner._l10n_sk_get_dic()
        if not dic:
            skipped.append((partner.id, "no DIČ recorded — enter it to publish this partner on Peppol"))
            continue
        # What core would have put there for 9950 is the sanitised VAT.
        expected = (partner.vat or "").strip().upper().replace(" ", "")
        current = (partner.peppol_endpoint or "").strip().upper()
        if current and current != expected:
            skipped.append((partner.id, "hand-set endpoint %r" % partner.peppol_endpoint))
            continue
        partner.write({"peppol_eas": "0245", "peppol_endpoint": dic})
        moved |= partner

    _logger.info(
        "l10n_sk_ubl_bis3: moved %s Slovak partner(s) from 9950 to 0245.",
        len(moved),
    )
    for partner_id, why in skipped:
        _logger.warning(
            "l10n_sk_ubl_bis3: res.partner(%s) left on 9950 — %s.",
            partner_id, why,
        )
