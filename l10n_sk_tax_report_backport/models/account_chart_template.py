# Copyright 2026 Data Dance s.r.o.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
"""Backport of the Odoo 19.0 core ``l10n_sk`` VAT tax template + report-tag set
onto the smaller 18.0 ``l10n_sk`` chart.

18.0 CE ``l10n_sk`` ships 7 taxes and NO tax tags; 19.0 CE ships 43 taxes
(rate + service/goods scope + RC/intra-EU/import/customs/bad-debt/... variants)
each bound to the DPH report tags. These ``@template('sk', ...)`` methods run in
the ``sk`` pass of ``_get_chart_template_data`` — AFTER core's None-code loader
parses the base ``l10n_sk`` CSV — so their data is merged on top of (and adds
the missing taxes to) any SK company's chart.

Tag references are XML-IDs (``l10n_sk_tax_report_backport.tag_sk_<code>``), not
bare names: 18.0's ``_deref_account_tags`` only touches the CSV parsed by core,
not the data returned by these ``@template`` methods, so a bare name would reach
``_load_data.deref_values`` and crash as ``account.<company>_<name>``. The tags
are created (with those XML-IDs) in ``data/account_tax_report_tags.xml``.
"""
from odoo import Command, models
from odoo.addons.account.models.chart_template import template

MODULE = "l10n_sk_tax_report_backport"


def _rep(rtype, doc, tag=None, account=None, factor=None):
    """One repartition-line Command for template tax data. ``tag`` is a bare DPH
    code (e.g. ``03``); it is referenced by the XML-ID of the tag created in
    ``data/account_tax_report_tags.xml`` (see module docstring for why)."""
    vals = {"repartition_type": rtype, "document_type": doc}
    if account:
        vals["account_id"] = account
    if factor is not None:
        vals["factor_percent"] = factor
    if tag:
        vals["tag_ids"] = "%s.tag_sk_%s" % (MODULE, tag)
    return Command.create(vals)


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("sk", "account.tax.group")
    def _get_sk_tax_report_backport_tax_group(self):
        """18.0 CE ``l10n_sk`` has no 5 % VAT group; 19.0 does. Add it so the
        backported 5 % taxes have a group to sit in."""
        return {
            "tax_group_vat_5": {
                "name": "VAT 5%",
                "name@sk": "DPH 5%",
                "country_id": "base.sk",
            },
        }

    @template("sk", "account.tax")
    def _get_sk_tax_report_backport_taxes(self):
        """The full 19.0 SK VAT tax set (43 taxes) with DPH report tags.

        Parsed from this module's ``data/template/account.tax-sk.csv`` (adapted
        from 19.0 core: unsupported columns dropped, ``tag_ids`` rewritten to
        XML-IDs). Merged over the 5 taxes 18.0 already ships (vy_tuz_23/19/0,
        vs_tuz_23/19 — repartition replaced to add tags) and adds the 38 new
        ones (5 % rate, service/goods scope, RC, intra-EU, triangular, import,
        customs, bad-debt, § 53b unpaid, special-regime)."""
        return self._parse_csv("sk", "account.tax", module=MODULE)

    @template("sk", "account.tax")
    def _get_sk_tax_report_backport_legal_notes(self):
        """Invoice legal mentions for the intra-EU sale taxes (19.0 parity).

        19.0's ``account.tax-sk.csv`` carries ``invoice_legal_notes`` (+ an
        ``@sk`` translation) on the three intra-EU *sale* taxes only — the EU
        directive article that has to be printed on the invoice. RC / import /
        export taxes carry **no** legal note in 19.0, so none is set here.

        ⚠️ 18.0's ``account.tax.invoice_legal_notes`` is a plain ``fields.Html``
        WITHOUT ``translate=True`` (19.0 added the flag). The field therefore
        stores a single value: the English base below is what is persisted and
        printed. The ``@sk`` variant is supplied for faithfulness to the 19.0
        row but is inert on 18.0 (the chart-template translation pass only
        touches fields whose ``translate`` attribute is True), so it neither
        applies nor errors.

        These bind onto the taxes already parsed from this module's CSV via a
        plain ``dict.update`` merge in ``_get_chart_template_data``."""
        return {
            "vy_eu_s": {
                "invoice_legal_notes":
                    "VAT Reverse charge - Article 196 of the Directive "
                    "2006/112/EC",
                "invoice_legal_notes@sk":
                    "Obrátené zdanenie DPH - článok 196 smernice 2006/112/ES",
            },
            "vy_eu_m": {
                "invoice_legal_notes":
                    "Exempt intra-community supplies - Article 138 of the "
                    "Directive 2006/112/EC",
                "invoice_legal_notes@sk":
                    "Oslobodené dodávky v rámci Spoločenstva - článok 138 "
                    "smernice 2006/112/ES",
            },
            "vy_eu_t": {
                "invoice_legal_notes":
                    "Exempt triangular transaction - Article 141 of the "
                    "Directive 2006/112/EC",
                "invoice_legal_notes@sk":
                    "Oslobodené trojstranné transakcie - článok 141 smernice "
                    "2006/112/ES",
            },
        }

    @template("sk", "account.fiscal.position")
    def _get_sk_tax_report_backport_fiscal_positions(self):
        """Fiscal-position tax auto-substitution (19.0 invoice-side parity).

        19.0's ``account.tax-sk.csv`` carries ``fiscal_position_ids`` /
        ``original_tax_ids`` columns that auto-swap a domestic tax to its
        intra-EU / export counterpart based on the customer's fiscal position.
        18.0's tax template does NOT support those columns, so the same effect
        is produced here with classic ``account.fiscal.position.tax`` mapping
        records (``position_id`` / ``tax_src_id`` / ``tax_dest_id``).

        Taxes are referenced by their bare template names; ``self.ref`` resolves
        them to the company instances (``account.<company>_<name>``).

        Because ``_get_chart_template_data`` merges each ``@template`` record
        with ``dict.update``, the ``tax_ids`` returned here for the positions
        18.0 core already ships (``..._1`` / ``fp_intra_private`` / ``..._2``)
        REPLACE the value core parsed from ``account.fiscal.position-sk.csv``
        (whose EU-intra rows still point at the pre-19.0 tax names
        ``vy_dod_eu`` / ``vs_nad_eu``) — so the mapping is the 19.0 set, not a
        superset. ``fiscal_position_template_3`` (Export Outside EU) is absent
        from 18.0 core, so it is created here to carry the export swaps."""
        def fp_tax(src, dest):
            return Command.create({"tax_src_id": src, "tax_dest_id": dest})

        # Domestic / EU-private (B2C): disambiguate the generic rate to its
        # goods-scoped variant (19.0 does this on both positions).
        goods = [
            ("vy_tuz_23", "vy_tuz_23_m"), ("vy_tuz_19", "vy_tuz_19_m"),
            ("vy_tuz_5", "vy_tuz_5_m"), ("vy_tuz_0", "vy_tuz_0_m"),
        ]
        # EU intra-community B2B: services -> EU services, goods -> EU goods,
        # purchases -> EU acquisition (the 5 % legs are new in the backport).
        eu_intra = [
            ("vy_tuz_23_s", "vy_eu_s"), ("vy_tuz_19_s", "vy_eu_s"),
            ("vy_tuz_5_s", "vy_eu_s"), ("vy_tuz_0_s", "vy_eu_s"),
            ("vy_tuz_23", "vy_eu_m"), ("vy_tuz_19", "vy_eu_m"),
            ("vy_tuz_5", "vy_eu_m"), ("vy_tuz_0", "vy_eu_m"),
            ("vs_tuz_23", "vs_nad_eu_23"), ("vs_tuz_19", "vs_nad_eu_19"),
            ("vs_tuz_5", "vs_nad_eu_5"),
        ]
        # Export outside the EU: every domestic sale rate/scope -> 0 % export.
        export = [
            ("vy_tuz_23", "vy_mimo_eu"), ("vy_tuz_23_s", "vy_mimo_eu"),
            ("vy_tuz_19", "vy_mimo_eu"), ("vy_tuz_19_s", "vy_mimo_eu"),
            ("vy_tuz_5", "vy_mimo_eu"), ("vy_tuz_5_s", "vy_mimo_eu"),
            ("vy_tuz_0", "vy_mimo_eu"), ("vy_tuz_0_s", "vy_mimo_eu"),
        ]
        return {
            "fiscal_position_template_1": {
                "tax_ids": [fp_tax(s, d) for s, d in goods]},
            "fp_intra_private": {
                "tax_ids": [fp_tax(s, d) for s, d in goods]},
            "fiscal_position_template_2": {
                "tax_ids": [fp_tax(s, d) for s, d in eu_intra]},
            "fiscal_position_template_3": {
                "name": "Export Outside EU",
                "name@sk": "Vývoz mimo EU",
                "sequence": 40,
                "auto_apply": True,
                "country_id": False,
                "country_group_id": False,
                "tax_ids": [fp_tax(s, d) for s, d in export]},
        }

    @template("sk", "account.tax")
    def _get_sk_tax_report_backport_legacy_taxes(self):
        """Keep the two 18.0-only legacy taxes tagged.

        19.0 renamed ``vy_dod_eu`` -> ``vy_eu_m`` and ``vs_nad_eu`` ->
        ``vs_nad_eu_23``, but 18.0 core still ships the old names. They stay in
        the chart, so bind the same DPH tags the 19.0 successors carry (14 for
        the intra-EU supply; 07/19/08 + 24_PR/28/25 for the acquisition), so
        existing bookings on them keep feeding the VAT return.

        ``vs_nad_eu`` is also renamed (append " (18.0)") to break the tax-name
        uniqueness collision with its 19.0 successor ``vs_nad_eu_23`` — both are
        purchase / "23% EU" / SK, which 18.0's ``_constrains_name`` rejects."""
        s343220, s343120 = "chart_sk_343220", "chart_sk_343120"
        return {
            "vy_dod_eu": {"repartition_line_ids": [
                _rep("base", "invoice", tag="14"),
                _rep("tax", "invoice"),
                _rep("base", "refund", tag="14"),
                _rep("tax", "refund"),
            ]},
            "vs_nad_eu": {"name": "23% EU (18.0)", "repartition_line_ids": [
                _rep("base", "invoice", tag="07"),
                _rep("tax", "invoice", tag="19", account=s343120),
                _rep("tax", "invoice", tag="08", account=s343220, factor=-100),
                _rep("base", "refund", tag="24_PR"),
                _rep("tax", "refund", tag="28", account=s343120),
                _rep("tax", "refund", tag="25", account=s343220, factor=-100),
            ]},
        }
