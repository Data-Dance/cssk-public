# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Teach core ``_map_eu_taxes`` the Slovak 5 % rate without editing core.

Core looks every mapping up in a module-level dict,
``odoo.addons.l10n_eu_oss.models.res_company.EU_TAX_MAP``, from inside one long
method. There is no hook between the lookup and the tax creation, and
re-implementing the creation (tax groups, the OSS payable/receivable accounts,
the xmlids core keys them on) to post-process its result would fork forty
lines of core that core keeps changing.

So the LOOKUP is overridden instead, and scoped:

* the module global is replaced once by a read-through view of the original
  dict. It answers exactly as the original does unless an overlay is active;
* the overlay lives in a ``ContextVar`` that only ``_map_eu_taxes`` below sets,
  for the duration of the core call.

Why the scoping matters: the Python module is shared by every database the
server process holds, including databases where this module is NOT
installed. Mutating the dict itself would hand those databases Slovak 5 %
mappings they never asked for. A ``ContextVar`` is local to the thread (and
to the greenlet under gevent), so a concurrent mapping run in another database
or request cannot see it either.
"""

import contextvars
from collections.abc import Mapping

from odoo import models
from odoo.addons.l10n_eu_oss.models import res_company as oss_res_company

from .eu_rates import sk_five_percent_overlay

_OVERLAY = contextvars.ContextVar("cssk_oss_eu_tax_map_overlay", default=None)


class ScopedEuTaxMap(Mapping):
    """``EU_TAX_MAP`` as core sees it, plus the overlay while one is active."""

    def __init__(self, base):
        self._base = base

    @property
    def base(self):
        return self._base

    def _overlay(self):
        return _OVERLAY.get() or {}

    def __getitem__(self, key):
        overlay = self._overlay()
        if key in overlay:
            return overlay[key]
        return self._base[key]

    def __iter__(self):
        yield from {**self._base, **self._overlay()}

    def __len__(self):
        return len({**self._base, **self._overlay()})


def _install_scoped_map():
    current = oss_res_company.EU_TAX_MAP
    if not isinstance(current, ScopedEuTaxMap):
        oss_res_company.EU_TAX_MAP = ScopedEuTaxMap(current)
    return oss_res_company.EU_TAX_MAP


_SCOPED_MAP = _install_scoped_map()


class ResCompany(models.Model):
    _inherit = "res.company"

    def _map_eu_taxes(self):
        """Run core's mapping with the Slovak 5 % entries visible to it.

        See the module docstring for why this is an overlay rather than an
        edit, and ``eu_rates.sk_five_percent_overlay`` for what it adds.
        """
        scoped = _install_scoped_map()
        token = _OVERLAY.set(sk_five_percent_overlay(scoped.base))
        try:
            res = super()._map_eu_taxes()
            self._cssk_oss_link_unmapped_taxes(scoped)
            return res
        finally:
            _OVERLAY.reset(token)

    def _cssk_oss_link_unmapped_taxes(self, scoped):
        """Map every domestic tax whose OSS counterpart already exists.

        19.0 core links a domestic tax to an OSS tax only when it CREATES that
        OSS tax; a second domestic tax mapping to the same foreign rate is
        skipped. 18.0 wrote a mapping line for every domestic tax, so this is
        a regression of the fiscal-position rewrite, and it is the one that
        defeats the Slovak 5 % rate outright: SK 5 % maps to exactly the
        foreign rates SK 19 % maps to, so whichever of the two core meets
        second is left unmapped — and an unmapped tax on an OSS sale charges
        the DOMESTIC rate. The same gap leaves the chart's per-rate variants
        (the Slovak ``_s`` / ``_m`` taxes) unmapped.

        Only links; never creates a tax or changes an existing link, so an
        accountant's own mapping is untouched. Runs inside the overlay, so it
        resolves rates exactly as the core pass just did.
        """
        eu_countries = self.env.ref("base.europe").country_ids
        oss_tag = self.env.ref("l10n_eu_oss.tag_oss")
        Tax = self.env["account.tax"]
        for company in self:
            # the company core instantiated the OSS taxes on
            company = (company.parent_ids.filtered(lambda c: c.vat)[-1:]
                       or company.root_id)
            domestic = Tax.search([
                *Tax._check_company_domain(company),
                ("type_tax_use", "=", "sale"),
                ("amount_type", "=", "percent"),
            ]).filtered(lambda t: not (
                (t.invoice_repartition_line_ids.tag_ids
                 | t.refund_repartition_line_ids.tag_ids) & oss_tag))
            positions = self.env["account.fiscal.position"].search([
                ("company_id", "=", company.id),
                ("country_id", "in",
                 (eu_countries - company.account_fiscal_country_id).ids),
                ("auto_apply", "=", True),
                ("vat_required", "=", False),
                ("foreign_vat", "=", False),
            ])
            for fpos in positions:
                foreign = {t.amount: t for t in fpos.tax_ids
                           if t.amount_type == "percent"}
                for tax in domestic - fpos.tax_ids.original_tax_ids:
                    rate = scoped.get((tax.country_id.code, tax.amount,
                                       fpos.country_id.code))
                    if rate and rate in foreign:
                        foreign[rate].original_tax_ids = [(4, tax.id)]
