# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import models

from odoo.addons.account.models.chart_template import template

#: Received EU services — self-assessed under § 69 ods. 3, reported in
#: r09/r09a/r09b of the return and in KV oddiel B.1.
_logger = logging.getLogger(__name__)

SK_EU_SERVICE_TAXES = ("vs_eu_s_23", "vs_eu_s_19", "vs_eu_s_5")

#: Stock ``l10n_sk`` taxes that carry tag ``14`` and must not.
#:
#: r14 is "základ dane za dodané tovary oslobodené od dane podľa § 43 ods. 1
#: a 4" — GOODS only (DPHv25 poučenie bod 31, the same wording in every vzor
#: since 2012, where it is r16). A B2B service to another member state is not
#: exempt at all: its place of supply is abroad (§ 15 ods. 1), so it is on no
#: row of the return and only on the súhrnný výkaz. The first buyer of a
#: trojstranný obchod is excluded in so many words: "prvý odberateľ neuvádza do
#: riadkov 13 a 14 hodnotu tovaru fakturovanú druhému odberateľovi". Stock
#: tags both ``14``, which put every EU service on r14 — measured on a POHODA
#: SK agenda as 23–57 k€ a month on r14 against 0.00 in all nine filed returns.
SK_NOT_ON_R14 = ("vy_eu_s", "vy_eu_t")


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    def _load(self, template_code, company, install_demo, force_create=True):
        result = super()._load(
            template_code, company, install_demo, force_create=force_create)
        if template_code == "sk":
            # After super(): a reload rewrites the taxes from the template and
            # brings tag 14 back with them.
            self._cssk_sk_drop_r14_tag(company or self.env.company)
        return result

    def _cssk_sk_drop_r14_tag(self, companies):
        """Take tag 14 off ``SK_NOT_ON_R14``, on the taxes and on posted lines.

        A post-load step rather than a template override: it leaves the rest
        of the stock repartition alone, so an upstream change to these taxes
        still arrives.

        The taxes alone would fix new documents only: a move line keeps the
        tags it was posted with, so every service invoice already booked would
        stay on r14. Those lines are retagged from the taxes' CURRENT
        repartition — a base line of one of these taxes keeps 14 only if one
        of its taxes still has it — which makes this idempotent and independent
        of how the chart got here. Written with SQL because ``tax_tag_ids`` is
        lock-date protected, and a company with a tax lock date would otherwise
        abort the upgrade or come out half-retagged. Draft lines are included
        on purpose: they would otherwise post with the stale tag.

        Returns the number of move lines retagged.
        """
        sk = self.env.ref("base.sk")
        tags = self.env["account.account.tag"]._get_tax_tags("14", sk.id)
        if not tags:
            return 0
        retagged = 0
        for company in companies:
            loader = self.with_company(company)
            taxes = self.env["account.tax"]
            for xmlid in SK_NOT_ON_R14:
                tax = loader.ref(xmlid, raise_if_not_found=False)
                if tax:
                    taxes |= tax
            if not taxes:
                continue
            reps = (taxes.invoice_repartition_line_ids
                    | taxes.refund_repartition_line_ids).filtered(
                        lambda r: r.tag_ids & tags)
            for rep in reps:
                rep.tag_ids -= tags
            self.env.flush_all()
            self.env.cr.execute(
                """
                DELETE FROM account_account_tag_account_move_line_rel rel
                 USING account_move_line aml
                 WHERE rel.account_move_line_id = aml.id
                   AND rel.account_account_tag_id = ANY(%(tags)s)
                   AND aml.company_id = %(company)s
                   AND aml.tax_repartition_line_id IS NULL
                   AND EXISTS (
                       SELECT 1 FROM account_move_line_account_tax_rel lt
                        WHERE lt.account_move_line_id = aml.id
                          AND lt.account_tax_id = ANY(%(taxes)s))
                   AND NOT EXISTS (
                       SELECT 1
                         FROM account_move_line_account_tax_rel lt
                         JOIN account_tax_repartition_line r
                           ON r.tax_id = lt.account_tax_id
                          AND r.repartition_type = 'base'
                         JOIN account_account_tag_account_tax_repartition_line_rel rt
                           ON rt.account_tax_repartition_line_id = r.id
                        WHERE lt.account_move_line_id = aml.id
                          AND rt.account_account_tag_id = ANY(%(tags)s))
             RETURNING aml.date
                """,
                {"tags": tags.ids, "company": company.id, "taxes": taxes.ids},
            )
            dates = [row[0] for row in self.env.cr.fetchall()]
            if dates:
                retagged += len(dates)
                _logger.info(
                    "l10n_sk_vat_return: tag 14 (r14) taken off %s posted "
                    "line(s) of %s dated %s to %s — EU services and the first "
                    "buyer's trojstranný obchod are not § 43 goods; returns "
                    "for those periods now recompute without them",
                    len(dates), company.display_name, min(dates), max(dates))
        if retagged:
            self.env["account.move.line"].invalidate_model(["tax_tag_ids"])
        return retagged

    @template("sk", "account.tax")
    def _get_sk_vat_return_account_tax(self):
        """Received EU services, and the domestic taxes they are mapped from.

        Stock ``l10n_sk`` maps every domestic purchase tax, under the "Eu
        intra" fiscal position, to the ``vs_nad_eu_*`` taxes — the acquisition
        of GOODS from another member state, row 07/08 of the return. A service
        bought from an EU supplier is not an acquisition of goods: the place of
        supply is Slovakia and the recipient self-assesses under § 69 ods. 3,
        row 09/10. It was filed in the wrong row, and Odoo's mapping cannot
        tell the two apart, because a fiscal position maps a tax to a tax and
        never looks at the product.

        The chart already solves this on the SALE side by splitting the source:
        ``23% S`` (services) maps to ``0% EÚ S`` and ``23% T`` to ``0% EÚ T``.
        This does the same for purchases: domestic ``23% S`` / ``19% S`` /
        ``5% S`` purchase taxes with the Services scope, mapped under "Eu intra"
        to ``23% EÚ S`` / ``19% EÚ S`` / ``5% EÚ S``, which carry the
        repartition of the chart's own ``vs_rc_*`` (r09b/r10b, r09/r10,
        r09a/r10a). A service product gets the ``S`` tax as its vendor tax;
        goods keep the plain one and still map to the acquisition of goods.

        Reported by an external accountant: "Base odoo chýba nastavenie
        fiškálnej pozície na RC."
        """
        data = self._parse_csv("sk", "account.tax", module="l10n_sk_vat_return")
        self._deref_account_tags("sk", data)
        # The control statement routes self-assessment by this flag; set it
        # where the control statement is installed, and leave the field alone
        # where it is not (it belongs to l10n_cssk_kv_kh_base, which the VAT
        # return does not depend on). The KV module flags the same xmlids on
        # its own install, for the opposite installation order.
        if "cssk_control_is_reverse_charge" in self.env["account.tax"]._fields:
            for xmlid in SK_EU_SERVICE_TAXES:
                if xmlid in data:
                    data[xmlid]["cssk_control_is_reverse_charge"] = True
        return data

    def _cssk_load_sk_eu_service_taxes(self, companies):
        """Load the taxes above into companies that already have the chart.

        ``@template`` data only materialises when a chart is loaded, so an
        existing company would never get them. Reuses the chart loader for the
        same xmlids, company prefixing and tag/account dereferencing a fresh
        load produces — but ONLY for the taxes the company lacks: ``_load_data``
        rewrites an existing record and appends repartition lines to it, and a
        full ``try_loading`` duplicates nine stock ``l10n_sk`` taxes per run.
        """
        loaded = 0
        for company in companies:
            loader = self.sudo().with_company(company)
            # Parsed per company: the loader consumes the dicts it is given.
            data = loader._get_sk_vat_return_account_tax()
            missing = {
                xmlid: vals for xmlid, vals in data.items()
                if not loader.ref(xmlid, raise_if_not_found=False)
            }
            if not missing:
                continue
            # A company that deleted "Eu intra" or a VAT tax group cannot take
            # these taxes as shipped. That must cost it the taxes, not cost
            # every company the module: this runs in the install hook and the
            # upgrade, where one raise aborts the whole operation.
            try:
                with self.env.cr.savepoint():
                    loader._load_data({"account.tax": missing})
            except Exception:
                _logger.warning(
                    "EU-service taxes not loaded for %s — its chart lacks "
                    "something they refer to (fiscal position \"Eu intra\", "
                    "a VAT tax group or a tax account); create them by hand",
                    company.display_name, exc_info=True)
                continue
            loaded += len(missing)
        return loaded
