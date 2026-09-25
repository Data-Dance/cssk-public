# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

#: Slovak VAT rates that are no longer in force, as
#: ``(rate, source_rate, valid_from, valid_to)``. ``source_rate`` is the
#: **current** rate whose taxes are cloned, and therefore which statutory slots
#: the historical rate reports in — a standard rate from the standard rate, a
#: reduced one from a reduced one.
#:
#: Rate history under zákon č. 222/2004 Z. z. o dani z pridanej hodnoty, § 27:
#:
#: * 2004-01-01 – 2006-12-31   19 %, single rate
#: * 2007-01-01 – 2010-12-31   19 % standard, 10 % reduced
#: * 2011-01-01 – 2024-12-31   20 % standard, 10 % reduced
#: * 2023-01-01 –              5 % reduced added (§ 27 ods. 2 písm. b))
#: * 2025-01-01 –              23 % standard, 19 % and 5 % reduced
#:
#: **The 19 % standard rate of 2004–2010 is deliberately absent.** 19 % is a
#: *current* rate in the Slovak chart — the reduced one, since 2025 — so a
#: document at 19 % already has taxes to map onto and the amount computed is
#: right. Only the return slot would differ, standard versus reduced, and a
#: second family of taxes named ``19%`` would collide with the live one by name
#: for the sake of agendas older than 2011. If an agenda that old ever has to be
#: imported, add it here with names that distinguish it, and expect the slot to
#: need checking rather than cloning.
#: The reverse-charge band was ONE line until the vzor of 1. 7. 2025 split it
#: by rate — ``dph2021.xsd`` defines ``r09``/``r10`` and no lettered variants,
#: ``dph2025.xsd`` adds ``r09a``/``r09b``/``r10a``/``r10b``. So a 20 % clone of
#: today's 23 % inherits tags ``09b``/``10b``, lines that did not exist while
#: 20 % was in force, and files on them: measured by the MRP extractor against
#: a filed FY2024 return as 804.03 of base and 160.81 of tax on r09b where the
#: filing uses r09.
#:
#: 10 % is cloned from 19 %, which carries ``09``/``10`` in the current form
#: because 19 % is the reduced band — the same tags the old single band used —
#: so it needs no remap. Only the standard rate moved.
SK_PRE_2025_RC_BAND = {"09b": "09", "10b": "10"}

SK_HISTORIC_VAT_RATES = (
    (20.0, 23.0, "2011-01-01", "2024-12-31", SK_PRE_2025_RC_BAND),
    (10.0, 19.0, "2007-01-01", "2024-12-31"),
)


class ResCompany(models.Model):
    _inherit = "res.company"

    def _cssk_historic_vat_rates(self):
        self.ensure_one()
        if self.chart_template == "sk":
            return SK_HISTORIC_VAT_RATES
        return super()._cssk_historic_vat_rates()
