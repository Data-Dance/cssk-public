# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
import re

from odoo import models

_logger = logging.getLogger(__name__)

#: Czech VAT rates that are no longer in force, as
#: ``(rate, source_rate, valid_from, valid_to)``. ``source_rate`` is the
#: **current** rate whose taxes are cloned, and therefore which statutory slots
#: the historical rate reports in — a standard rate from the standard rate, a
#: reduced one from a reduced one.
#:
#: Rate history under zákon č. 235/2004 Sb. o dani z přidané hodnoty, § 47:
#:
#: * 2004-05-01 – 2007-12-31   19 % základní, 5 % snížená
#: * 2008-01-01 – 2009-12-31   19 % základní, 9 % snížená
#: * 2010-01-01 – 2011-12-31   20 % základní, 10 % snížená
#: * 2012-01-01 – 2012-12-31   20 % základní, 14 % snížená
#: * 2013-01-01 – 2014-12-31   21 % základní, 15 % snížená
#: * 2015-01-01 – 2023-12-31   21 % základní, 15 % první a 10 % druhá snížená
#: * 2024-01-01 –              21 % základní, 12 % snížená
#:
#: Reaching back to 2004-05-01 is not arbitrary: that is when the current VAT
#: Act took effect, on EU accession, and it is the earliest date whose documents
#: this localisation's statements are built to describe at all.
#:
#: **10 % gets one entry, not two.** It was the reduced rate from 2010 to 2011
#: and the *second* reduced rate from 2015 to 2023, with three years between in
#: which it did not exist. Two taxes at the same rate would be
#: indistinguishable to whoever has to pick one, so it is a single tax spanning
#: both, and the gap is recorded here rather than in the data.
CZ_HISTORIC_VAT_RATES = (
    (20.0, 21.0, "2010-01-01", "2012-12-31"),
    (19.0, 21.0, "2004-05-01", "2009-12-31"),
    (15.0, 12.0, "2013-01-01", "2023-12-31"),
    (14.0, 12.0, "2012-01-01", "2012-12-31"),
    (10.0, 12.0, "2010-01-01", "2023-12-31"),
    (9.0, 12.0, "2008-01-01", "2009-12-31"),
    (5.0, 12.0, "2004-05-01", "2007-12-31"),
)


#: ``l10n_cz`` intra-Community acquisition tax -> the domestic purchase tax it
#: replaces under the Intra-Community fiscal position. ``l10n_cz`` ships these
#: four with an empty ``original_tax_ids`` (the Extra-Community ones are
#: mapped), so the position maps nothing and an EU vendor bill keeps the
#: domestic 21 % / 12 % charged by the supplier instead of self-assessing.
CZ_INTRA_COMMUNITY_PURCHASE_MAP = {
    "l10n_cz_21_acquisition_goods_eu": "l10n_cz_21_receipt_domestic_supplies",
    "l10n_cz_12_purchase_goods_eu": "l10n_cz_12_receipt_domestic_supplies",
    "l10n_cz_21_receipt_service_person_eu":
        "l10n_cz_21_receipt_domestic_services",
    "l10n_cz_12_receipt_service_person_eu":
        "l10n_cz_12_receipt_domestic_service",
}


class ResCompany(models.Model):
    _inherit = "res.company"

    def _cz_map_intra_community_purchase_taxes(self):
        """Let the Intra-Community position replace the domestic purchase tax.

        Found on an inter-company bill from a Slovak seller to a Czech buyer:
        30.00 of goods came out at 36.30, the supplier being asked for Czech
        21 % that the buyer has to self-assess instead. Every Czech vendor bill
        from an EU supplier does the same, because ``map_tax`` passes a tax
        through untouched when no destination names it as its original.

        Goods map to ``EU G`` and services to ``EU S`` by the domestic tax the
        product carries (``21% G`` / ``21% S``), which is the only signal of
        goods-versus-service Odoo gives the position.

        Only links are added, never removed, so a mapping a user has set up
        by hand survives. Idempotent. Archived historical rate clones are left
        alone: nothing picks them on a new document.
        """
        if "original_tax_ids" not in self.env["account.tax"]._fields:
            # 18.0 ONLY, AND A DELIBERATE NO-OP. This mapping is written
            # against 19.0's tax-alternatives rework: a destination tax names
            # the domestic taxes it replaces (``account.tax.original_tax_ids``,
            # with ``fiscal_position_ids``, ``replacing_tax_ids`` and
            # ``is_domestic`` beside it), and 19.0 core ``l10n_cz`` ships a
            # ``fiscal_position_intra_community`` for it to act on.
            #
            # 18.0 has none of that. Its ``account.tax`` carries no such field;
            # a position maps taxes through ``account.fiscal.position.tax``
            # rows (``tax_src_id`` -> ``tax_dest_id``); and 18.0 core
            # ``l10n_cz`` has no intra-Community position at all — only
            # ``fiscal_position_domestic_cz`` and
            # ``fiscal_position_eu_private_cz``, the latter being private (B2C)
            # trade, not a B2B acquisition.
            #
            # So the fix cannot be ported: on this series it would mean
            # CREATING a fiscal position and its mapping rows, which is a
            # client-visible design decision and not a translation of the 19.0
            # code. Left undone on purpose, recorded in CHANGELOG.rst under
            # "Carry-over to 18.0", and logged rather than passed over in
            # silence — a Czech vendor bill from an EU supplier keeps its
            # domestic 21 % on this branch, which is the bug 1.7.0 fixed on
            # 19.0 and which is still live here.
            _logger.warning(
                "l10n_cz_vat_return: the intra-Community purchase tax mapping "
                "is not applied on Odoo 18.0 — this series has neither "
                "account.tax.original_tax_ids nor a core intra-Community "
                "fiscal position. An EU vendor bill will keep the domestic "
                "rate and must be self-assessed by hand. See "
                "l10n_cz_vat_return/CHANGELOG.rst.")
            return 0
        ChartTemplate = self.env["account.chart.template"]
        touched = 0
        for company in self:
            if company.chart_template != "cz":
                continue
            ref = ChartTemplate.with_company(company).ref
            for dest_xmlid, src_xmlid in CZ_INTRA_COMMUNITY_PURCHASE_MAP.items():
                dest = ref(dest_xmlid, raise_if_not_found=False)
                src = ref(src_xmlid, raise_if_not_found=False)
                if not dest or not src:
                    # A company whose chart lacks one of these has deleted it
                    # or predates it; say so rather than leave the position
                    # silently half-mapped.
                    _logger.warning(
                        "l10n_cz_vat_return: %s has no %s, intra-Community "
                        "mapping not set", company.display_name,
                        dest_xmlid if not dest else src_xmlid,
                    )
                    continue
                if src in dest.original_tax_ids:
                    continue
                dest.original_tax_ids = [(4, src.id)]
                touched += 1
            if touched:
                _logger.info(
                    "l10n_cz_vat_return: %s intra-Community purchase tax "
                    "mapping(s) added on %s", touched, company.display_name,
                )
        return touched

    def _cssk_historic_vat_rates(self):
        self.ensure_one()
        if self.chart_template == "cz":
            return CZ_HISTORIC_VAT_RATES
        return super()._cssk_historic_vat_rates()


#: The declaration line a self-assessed purchase tax already reports on tells
#: us its RATE BAND, so the deduction band follows without a single rate
#: literal. ř3/ř5/ř10/ř12 are the základní-sazba declaration lines and ř4/ř6/
#: ř11/ř13 the snížená ones — which is why a chart that adds a rate needs no
#: change here.
CZ_SELFASSESSED_BAND = {
    "VAT 3 Base": "43", "VAT 5 Base": "43", "VAT 7 Base": "43",
    "VAT 10 Base": "43", "VAT 12 Base": "43",
    "VAT 4 Base": "44", "VAT 6 Base": "44", "VAT 8 Base": "44",
    "VAT 11 Base": "44", "VAT 13 Base": "44",
}

#: Rows whose self-assessed tax `l10n_cz` declares WITHOUT a deduction leg, so
#: the leg has to be created rather than merely tagged. See
#: ``_cz_build_selfassessed_deduction``.
#:
#: ⚠️ ř9 is deliberately absent. Rows 3-13 are all deductible on ř43/44 by the
#: form's own caption, but ř9 is *pořízení nového dopravního prostředku*, where
#: the deduction is not automatic — so its single leg may well be intended, and
#: nothing here has the evidence to overrule it.
CZ_SELFASSESSED_NO_LEG = ("VAT 7 Base", "VAT 8 Base")

#: The declaration tag of a self-assessed tax as the 18.0 chart writes it on
#: the −100 leg: signed, and the sign is the leg's. See
#: ``_cz_relocate_declaration_tag``.
CZ_SIGNED_DECLARATION_TAG = re.compile(r"^-VAT \d+ Tax$")

#: A declaration tag of EITHER sign, for recognising one left on a move line
#: by a chart that has since been relocated. See
#: ``_cz_retag_posted_selfassessed_lines``.
CZ_DECLARATION_TAG = re.compile(r"^[+-]?VAT \d+ Tax$")


def _cz_tag_key(name):
    """A tax tag's name as the tables above spell it.

    Odoo 18 names a tax tag with its sign — ``+VAT 3 Base`` on the invoice
    side, ``-VAT 3 Base`` on the refund side — and 19.0 dropped the sign
    (``VAT 3 Base``). The tables are written unsigned, so a signed name is
    looked up without its sign. Before this the 18.0 port matched nothing:
    every self-assessed tax read as "declares on no line this maps from",
    and ř43/ř44 computed 0.00 against 207 299 filed on the first Czech
    agenda compared on this series.
    """
    return name[1:] if name[:1] in "+-" else name


class ResCompanyCzDeduction(models.Model):
    _inherit = "res.company"

    def _cz_signed_tags(self):
        """Does this chart carry its tax tags signed (Odoo 18) or not (19.0)?

        Read off the chart rather than off the version: what matters is how
        the tags the taxes already carry are named, and the chart says so.

        Memoised per company for the duration of one hook run, through the
        ``cz_signed_tags`` context dict the callers seed: the answer cannot
        change while the hook runs, and asked afresh it is one query per tax
        per document type — which the migration pays once per company in the
        database.
        """
        self.ensure_one()
        memo = self.env.context.get("cz_signed_tags")
        if memo is not None and self.id in memo:
            return memo[self.id]
        country = self.account_fiscal_country_id
        signed = bool(country) and bool(self.env["account.account.tag"].search([
            ("name", "=like", "+VAT %"), ("applicability", "=", "taxes"),
            ("country_id", "=", country.id),
        ], limit=1))
        if memo is not None:
            memo[self.id] = signed
        return signed

    def _cz_deduction_tag(self, line, kind, document_type="invoice"):
        """The ř43/ř44 tag, created on first use.

        Named to match the chart's own convention for the other deduction
        lines — ``VAT 40 Base`` / ``VAT 40 Total`` for ř40 — so the four new
        tags read like the eight that were already there. `l10n_cz` defines
        none for 43/44: its tag list runs 40, 41, 42 and then jumps to 47.

        On a signed chart (Odoo 18) the tag is signed the way the chart signs
        its own: ``+`` on the invoice side, ``-`` (negating) on the refund
        side, so that ``_get_tax_tags`` finds it by its bare name like any
        other and Odoo's own report engine reads it like any other.
        """
        self.ensure_one()
        name = "VAT %s %s" % (line, kind)
        vals = {}
        if self._cz_signed_tags():
            refund = document_type == "refund"
            name = ("-" if refund else "+") + name
            vals["tax_negate"] = refund
        Tag = self.env["account.account.tag"]
        country = self.account_fiscal_country_id
        tag = Tag.search([
            ("name", "=", name), ("applicability", "=", "taxes"),
            ("country_id", "=", country.id),
        ], limit=1)
        if not tag:
            tag = Tag.create(dict(vals, name=name, applicability="taxes",
                                  country_id=country.id))
        return tag

    def _cz_relocate_declaration_tag(self, document_type, legs, deduction):
        """Odoo 18: put the declaration on the +100 leg, as 19.0's chart has it.

        19.0's ``l10n_cz`` tags the DECLARATION (``VAT 3 Tax``) on the +100
        leg and leaves the −100 leg bare; 18.0's tags it ``-VAT 3 Tax`` on the
        −100 leg. Under Odoo's own report engine the two agree — a negating
        tag on a credit reads positive — but ``cssk.vat.return`` sums raw
        balances with the formula's sign only, as 19.0's engine does, and on
        18.0 read the −100 leg's credit as −207 298.56 against 207 299 filed:
        magnitude right, sign inverted, on every self-assessed period.

        Moving the tag to the +100 leg, as ``+VAT 3 Tax``, makes both engines
        read +X: Odoo's because a plain tag on a debit is positive, ours
        because the leg's balance is. The refund side already has that shape
        on 18.0 (``-VAT 3 Tax`` on the +100 leg, a credit on a credit note)
        and is left alone. Unsigned charts have nothing to move.
        """
        self.ensure_one()
        if document_type != "invoice" or not self._cz_signed_tags():
            return 0
        positive = legs.filtered(lambda r: r.factor_percent > 0)[:1]
        if not positive:
            return 0
        Tag = self.env["account.account.tag"]
        moved = 0
        for tag in deduction.tag_ids.filtered(
                lambda t: CZ_SIGNED_DECLARATION_TAG.match(t.name or "")):
            plus = Tag.search([
                ("name", "=", "+" + tag.name[1:]),
                ("applicability", "=", "taxes"),
                ("country_id", "=", tag.country_id.id),
            ], limit=1)
            if not plus:
                # Cannot happen on a chart whose tax report declares the tag
                # — the pair is created with the expression — but say so
                # rather than leave the sign defect in place unannounced.
                _logger.warning(
                    "l10n_cz_vat_return: %s has no counterpart for %s, the "
                    "declaration stays on the deduction leg and ř%s will read "
                    "it with the wrong sign", self.display_name, tag.name,
                    _cz_tag_key(tag.name).split()[1],
                )
                continue
            if plus not in positive.tag_ids:
                positive.tag_ids = [(4, plus.id)]
            deduction.tag_ids = [(3, tag.id)]
            moved += 1
        return moved

    def _cz_retag_posted_selfassessed_lines(self):
        """Bring move lines posted BEFORE the relocation onto the new tags.

        ``_cz_relocate_declaration_tag`` moves a tag on the chart; a move line
        keeps the tags it was posted with. Those two facts together are worse
        than the defect they replace, because ``_get_tax_tags`` matches both
        signed variants of a name: an old line's ``-VAT 3 Tax`` on the output
        CREDIT leg is still summed raw as −210 while a new line's
        ``+VAT 3 Tax`` on the input DEBIT leg sums as +210, so in any period
        that straddles the upgrade the two CANCEL. Measured on a throwaway
        database, one pre-upgrade bill and one post-upgrade bill of 1 000 each:

            before the migration       ř3 base 1 000   ř3 tax −210   ř43 0.00
            after, history only        ř3 base 1 000   ř3 tax −210   ř43 0.00
            after, history + new bill  ř3 base 2 000   ř3 tax   0.00 ř43 210

        A period that should declare 420 declares nothing, with a base row
        that still reads a plausible 2 000. So the migration reconciles the
        posted lines too, from the repartition's CURRENT tags rather than from
        a journal of what moved — which makes it idempotent and independent of
        how the chart got into its present shape.

        Writes go through SQL on the tag relation, for one reason: a company
        with a tax lock date would otherwise take a ``UserError`` from
        ``account.move.line.write`` (``tax_tag_ids`` is tax-lock protected),
        which either aborts the whole upgrade or — worse, if caught per line —
        leaves exactly the half-retagged state above. Nothing filed from Odoo
        can depend on the old tags: they produced a NEGATIVE ř3, which no
        return could have carried. Balances, accounts and repartition links
        are not touched, only which row of the return reads them, so
        ``tax_tag_invert`` stays correct as computed.
        """
        AML = self.env["account.move.line"]
        Tax = self.env["account.tax"].with_context(active_test=False)
        retagged = 0
        for company in self:
            if company.chart_template != "cz":
                continue
            # The managed set, selected exactly as the hook selects it.
            managed = {}
            for tax in Tax.search([
                ("company_id", "=", company.id),
                ("type_tax_use", "=", "purchase"),
            ]):
                for document_type, reps in (
                    ("invoice", tax.invoice_repartition_line_ids),
                    ("refund", tax.refund_repartition_line_ids),
                ):
                    base = reps.filtered(lambda r: r.repartition_type == "base")
                    if not any(_cz_tag_key(t.name) in CZ_SELFASSESSED_BAND
                               for t in base.tag_ids):
                        continue
                    for rep in reps.filtered(
                            lambda r: r.repartition_type == "tax"):
                        managed[rep.id] = (tax, base)
            if not managed:
                continue
            add, drop = [], []
            lines = AML.search([
                ("company_id", "=", company.id),
                ("tax_repartition_line_id", "in", list(managed)),
            ])
            for line in lines:
                tax, base = managed[line.tax_repartition_line_id.id]
                wanted = line.tax_repartition_line_id.tag_ids
                have = line.tax_tag_ids
                add += [(line.id, t.id) for t in wanted - have]
                # Only a declaration tag the repartition no longer carries is
                # dropped — that is precisely the one that was relocated, and
                # nothing else on the line can match the shape.
                drop += [(line.id, t.id) for t in have - wanted
                         if CZ_DECLARATION_TAG.match(t.name or "")]
                # The base lines of the same document: additive only, since a
                # base line's tags are the union over every tax it carries.
                for bl in line.move_id.line_ids.filtered(
                        lambda l: tax in l.tax_ids):
                    add += [(bl.id, t.id) for t in base.tag_ids - bl.tax_tag_ids]
            add, drop = sorted(set(add)), sorted(set(drop))
            if add:
                self.env.cr.execute(
                    """INSERT INTO account_account_tag_account_move_line_rel
                            (account_move_line_id, account_account_tag_id)
                       SELECT * FROM unnest(%s::int[], %s::int[])
                       ON CONFLICT DO NOTHING""",
                    ([a for a, _t in add], [t for _a, t in add]),
                )
            if drop:
                self.env.cr.execute(
                    """DELETE FROM account_account_tag_account_move_line_rel
                       WHERE (account_move_line_id, account_account_tag_id)
                             IN (SELECT * FROM unnest(%s::int[], %s::int[]))""",
                    ([a for a, _t in drop], [t for _a, t in drop]),
                )
            if add or drop:
                self.env.invalidate_all()
                touched = lines.move_id
                retagged += len(touched)
                dates = touched.mapped("date")
                _logger.warning(
                    "l10n_cz_vat_return: retagged the self-assessed lines of "
                    "%s posted entries on %s (%s .. %s): ř3-13 and ř43/ř44 "
                    "now recompute differently for those periods than they "
                    "did before this upgrade",
                    len(touched), company.display_name,
                    min(dates) if dates else "-", max(dates) if dates else "-",
                )
        return retagged

    def _cz_fix_refund_repartition_accounts(self):
        """Give the refund side the tax account the invoice side already has.

        ``l10n_cz`` ships four reverse-charge purchase taxes — ``12% EU G``,
        ``21% EU G``, ``12% EU S``, ``21% EU S`` — whose INVOICE repartition
        names both legs (343112/343212, 343121/343221) while the REFUND
        repartition names only the deductible one. The self-assessed leg of a
        credit note therefore has no tax account, and Odoo leaves that amount
        on the BASE line's account instead.

        The consequence is not a misposted tax line but a **clearing account
        that stops clearing**: on a seven-year Czech import, 64 reverse-charge
        corrections left 289,031.99 sitting on účet 395000, which nets to zero
        in the source. Nothing else disagreed — the VAT return and the control
        statement both read tags, and the tags are right — so the only witness
        was the account balance.

        The invoice side states the intent, so it is copied rather than
        configured: same ``factor_percent``, same account. Historical rate
        clones inherit the defect from whatever they were cloned from and are
        fixed by the same pass, which is why this runs over every tax rather
        than a list of four xmlids.

        Deliberately does NOT touch the mirror case, ``0% EU S``, whose refund
        side names 343221 where the invoice side names nothing. That one posts
        100 % of a zero rate and moves no money; changing it would be a guess
        about intent with nothing measurable behind it.

        Idempotent: a leg that already has an account is left alone.
        """
        Tax = self.env["account.tax"].with_context(active_test=False)
        touched = 0
        for company in self:
            if company.chart_template != "cz":
                continue
            for tax in Tax.search([("company_id", "=", company.id)]):
                invoice = {
                    line.factor_percent: line.account_id
                    for line in tax.invoice_repartition_line_ids
                    if line.repartition_type == "tax" and line.account_id
                }
                for line in tax.refund_repartition_line_ids:
                    if line.repartition_type != "tax" or line.account_id:
                        continue
                    account = invoice.get(line.factor_percent)
                    if account:
                        line.account_id = account
                        touched += 1
            if touched:
                _logger.info(
                    "l10n_cz_vat_return: %s refund repartition account(s) "
                    "restored on %s", touched, company.display_name,
                )
        return touched

    def _cz_build_selfassessed_deduction(self, tax, document_type, base, legs):
        """Build the deduction leg `l10n_cz` leaves off ř. 7/8, or nothing.

        A self-assessed tax has TWO legs: the liability you declare and the
        deduction you claim, and they cancel — because the supplier charges no
        VAT, so nothing extra is owed to anybody. `l10n_cz` models EU
        acquisitions that way and models **import of goods with one leg only**.

        Measured on the shipped Czech chart, the same 1 000 CZK vendor bill::

            21% EU G   untaxed 1000.00  tax   0.00  TOTAL 1000.00
            21% EX G   untaxed 1000.00  tax 210.00  TOTAL 1210.00

        So Odoo asks the user to pay a supplier 1 210 against a 1 000 invoice.
        That is a wrong PAYABLE, not a reporting nicety, and it is wrong on its
        own terms whatever one concludes about ř43/44. The sibling `21% EX S`
        (services, ř. 12/13) already carries the leg, so goods and services
        currently disagree for no reason the form supports — ř43/44 reads "Ze
        zdanitelných plnění vykázaných na řádcích **3 až 13**", which contains
        7 and 8.

        It also breaks the document. With nothing to cancel the computed tax,
        the move stops balancing and Odoo silently adds an automatic balancing
        line: on a real agenda that put 912.87 onto 261000 *Peníze na cestě*,
        an account the source never touched.

        ⚠️ The account is taken from a SIBLING tax of the same rate that
        already has the two-leg shape — on the Czech chart that is the intra-EU
        acquisition, whose negative leg sits on the output account while the
        positive sits on the input one, so the liability and the deduction stay
        separately visible. Where no sibling exists the leg is put on the
        positive leg's own account, which still cancels correctly and is what
        the source systems themselves do; guessing an account code from
        another by string surgery is the one thing not done here.

        Returns the created line, or an empty recordset when the shape is not
        the one this repairs. Idempotent: it only ever fires on a tax with
        exactly one tax leg.
        """
        self.ensure_one()
        if len(legs) != 1 or not any(
            _cz_tag_key(t.name) in CZ_SELFASSESSED_NO_LEG for t in base.tag_ids
        ):
            return self.env["account.tax.repartition.line"]
        siblings = self.env["account.tax"].with_context(active_test=False).search([
            ("company_id", "=", self.id),
            ("type_tax_use", "=", tax.type_tax_use),
            ("amount", "=", tax.amount),
            ("amount_type", "=", tax.amount_type),
            ("id", "!=", tax.id),
        ])
        account = next(
            (rep.account_id
             for other in siblings
             # ⚠️ The sibling must be self-assessed ITSELF, and the leg must be
             # for the same document type. Without the first, an ordinary
             # purchase tax at the same rate qualifies and lends an account
             # that means something else; without the second, an invoice leg
             # can be built from a refund leg's account. They coincide on the
             # Czech chart, which is exactly why neither would have been
             # noticed here. Raised by a GPT-5.3-Codex review.
             if any(_cz_tag_key(t.name) in CZ_SELFASSESSED_BAND
                    for t in other.repartition_line_ids.filtered(
                        lambda r: r.repartition_type == "base").tag_ids)
             for rep in other.repartition_line_ids
             if rep.repartition_type == "tax"
             and rep.document_type == document_type
             and rep.factor_percent < 0
             and rep.account_id),
            legs.account_id,
        )
        return self.env["account.tax.repartition.line"].create({
            "tax_id": tax.id,
            "document_type": document_type,
            "repartition_type": "tax",
            "factor_percent": -100.0,
            "account_id": account.id if account else False,
            # Mirror the leg it is cancelling rather than relying on a default:
            # l10n_cz marks both tax legs of a reverse charge for the closing,
            # and a leg left out of it would quietly skip the VAT closing entry.
            "use_in_tax_closing": legs[:1].use_in_tax_closing,
            "sequence": max(legs.mapped("sequence") or [1]) + 1,
        })

    def _cz_tag_selfassessed_deduction(self):
        """Tag the deduction leg of every self-assessed Czech purchase tax.

        `l10n_cz` tags only the DECLARATION: a reverse charge or intra-EU
        acquisition carries ``VAT 3 Base``/``VAT 3 Tax`` on its base and +100
        legs and leaves the **−100 leg bare**, so the deduction the taxpayer is
        entitled to reaches no line of the return. Measured against 59 filed
        Řádné returns of a real Czech company, ř43 and ř44 computed 0.00 in
        **every** period against filed figures totalling 94.5M of base and
        14 534 001.54 of tax — while the output side of the same returns agreed
        to within 0.03 %.

        Confirmed with a second opinion (gpt-5.3-codex) before building:
        ř43/ř44 are the deduction of tax self-assessed on ř3–13, split
        základní/snížená, and they DO require a base as well as a tax figure;
        tagging the −100 leg is the right mechanism rather than deriving the
        deduction as an aggregate of ř3–13, because a partial or denied
        deduction makes that aggregate wrong; and the base repartition line
        needs the deduction base tag IN ADDITION to the declaration one.

        The band comes from the declaration tag the tax already carries, not
        from its rate — see ``CZ_SELFASSESSED_BAND`` — so a chart that adds a
        rate is handled without touching this.

        ``odkr_zdp*`` (krácený odpočet) stays manual on purpose: a partial
        claim is the taxpayer's coefficient, not a property of the tax.

        Idempotent: a leg already carrying its deduction tag is left alone.
        """
        self = self.with_context(cz_signed_tags={})
        Tax = self.env["account.tax"].with_context(active_test=False)
        touched = 0
        for company in self:
            if company.chart_template != "cz":
                continue
            taxes = Tax.search([
                ("company_id", "=", company.id),
                ("type_tax_use", "=", "purchase"),
            ])
            for tax in taxes:
                for document_type, reps in (
                    ("invoice", tax.invoice_repartition_line_ids),
                    ("refund", tax.refund_repartition_line_ids),
                ):
                    base = reps.filtered(lambda r: r.repartition_type == "base")
                    legs = reps.filtered(lambda r: r.repartition_type == "tax")
                    line = next(
                        (CZ_SELFASSESSED_BAND[_cz_tag_key(t.name)]
                         for t in base.tag_ids
                         if _cz_tag_key(t.name) in CZ_SELFASSESSED_BAND),
                        None,
                    )
                    if not line:
                        continue
                    if len(legs) < 2:
                        # `l10n_cz` declares ř. 7/8 with ONE leg, so there is
                        # nothing to tag until one is built. See
                        # _cz_build_selfassessed_deduction for why that is a
                        # defect rather than a choice.
                        built = company._cz_build_selfassessed_deduction(
                            tax, document_type, base, legs)
                        if not built:
                            continue
                        touched += 1
                        legs |= built
                    base_tag = company._cz_deduction_tag(
                        line, "Base", document_type)
                    total_tag = company._cz_deduction_tag(
                        line, "Total", document_type)
                    deduction = legs.filtered(
                        lambda r: r.factor_percent < 0)[:1]
                    if not deduction:
                        continue
                    touched += company._cz_relocate_declaration_tag(
                        document_type, legs, deduction)
                    if base_tag not in base.tag_ids:
                        base.tag_ids = [(4, base_tag.id)]
                        touched += 1
                    if total_tag not in deduction.tag_ids:
                        deduction.tag_ids = [(4, total_tag.id)]
                        touched += 1
            if touched:
                _logger.info(
                    "l10n_cz_vat_return: %s repartition tag(s) added for the "
                    "ř43/ř44 deduction on %s", touched, company.display_name,
                )
        return touched


#: A purchase tax earns a *Majetek* twin exactly when the acquisition it
#: models is deductible on ř. 40–44, because ř. 47 reports the asset share of
#: **that** deduction — "Hodnota pořízeného majetku vymezeného v § 4 odst. 4
#: písm. d) a e)", read against ř. 46 above it.
#:
#: The source tax already says which: ř40/ř41 for an ordinary domestic
#: purchase, and one of the ř3–ř13 declaration lines for a self-assessed one,
#: whose deduction this module puts on ř43/ř44. So the set is derived from
#: ``CZ_SELFASSESSED_BAND``, and a chart that adds a rate gets its twins
#: without a line changing here.
#:
#: Written unsigned and matched through ``_cz_tag_key``: the 18.0 chart signs
#: its tag names (``+VAT 40 Base``) and 19.0 does not.
#:
#: Three of the shipped purchase taxes are therefore left WITHOUT a twin, and
#: each absence is a decision:
#:
#: * ``21% Vehicle`` (ř. 9, pořízení nového dopravního prostředku) — a new
#:   means of transport is an asset by any reading, but this module
#:   deliberately does not claim its ř43/44 deduction (see
#:   ``CZ_SELFASSESSED_NO_LEG``). Reporting an asset on ř. 47 whose deduction
#:   appears nowhere in ř. 40–46 would make the two rows contradict each other.
#: * ``0% EX G.Custom`` (ř. 42, daň zaplacená celnímu orgánu) — an imported
#:   machine is a textbook ř. 47 case, but `l10n_cz` ships this tax at **0 %**,
#:   so its ``VAT 42 Total`` computes 0.00 and a twin would file an asset base
#:   against no tax. The defect is upstream in ř. 42 and is not fixed by
#:   duplicating it.
#: * ``0% EX G`` (ř. 32, osvobozené dovozy) — exempt, so nothing is deducted
#:   and nothing belongs on ř. 47.
CZ_ASSET_SOURCE_TAGS = frozenset(CZ_SELFASSESSED_BAND) | {
    "VAT 40 Base", "VAT 41 Base",
}

#: Suffixed, not prefixed. ``_cssk_historic_tax_name`` substitutes the LEADING
#: rate token, so a twin named ``Majetek 21%`` would never acquire its
#: historical rates — and the whole point of following the chart's
#: ``<rate>%[ qualifier]`` shape is that the historic generator then clones the
#: twins for free, across all seven Czech rate changes since 2004.
#:
#: Czech rather than English because it is the form's own word for the thing
#: (ř. 47 "...pořízeného **majetku**..."), it is what the Vario and Pohoda tax
#: position tables call it, and it is the word the accountant choosing it from
#: a dropdown is looking for: a term that IS the statute's own stays in the
#: national language, untranslated, while generic UI text is English.
CZ_ASSET_SUFFIX = "Majetek"


class ResCompanyCzAssetAcquisition(models.Model):
    _inherit = "res.company"

    def _cz_suffix_every_translation(self, source, twin):
        """Suffix the twin's name in EVERY language the source has one in.

        ``copy()`` carries the source's translations wholesale and the ``name``
        in the copy values overwrites only the language the pass happens to run
        under. Install under ``en_US`` and the Czech name of ``21% Majetek``
        stays "21 %" — the SOURCE's name — so the accountant picking a tax in
        Czech sees two entries reading "21 %" and no way to tell which reports
        on ř. 47.

        Not a duplicate-creation bug: the twin is found by
        ``cz_asset_source_tax_id``, not by name. It is a dropdown the user
        cannot use, which on this form is nearly as bad.
        """
        self.ensure_one()
        field = twin._fields["name"]
        if not field.translate:
            return False
        stored = field._get_stored_translations(source) or {}
        values = {
            lang: "%s %s" % (value, CZ_ASSET_SUFFIX)
            for lang, value in stored.items()
            # ``_get_stored_translations`` carries bookkeeping keys beginning
            # with an underscore alongside the real languages.
            if value and not lang.startswith("_")
        }
        if not values:
            return False
        return twin.update_field_translations("name", values)

    def _cz_asset_acquisition_tag_legs(self, tax):
        """Put the ř. 47 tags on one twin. Returns the number of changes.

        ``VAT 47 Base`` goes on the base repartition and ``VAT 47 Total`` on
        the **positive** tax leg(s), on the invoice and refund sides alike so a
        credit note takes the asset back off the row.

        ⚠️ The positive leg, specifically, and that is the whole reason this
        design works without touching the line definitions. ``od_maj`` reads
        ``VAT 47 Total`` **unsigned**, so the tag has to sit on a leg whose raw
        balance is positive on a vendor bill — the +100 leg, a debit. The −100
        leg of a self-assessed tax is a credit, and tagging it there would file
        ř. 47 negative, which is what happened to ř43/ř44 before their formulas
        were signed (see ``_cz_tag_selfassessed_deduction``).

        ⚠️ **Every** positive leg, not the first. A tax that splits its
        deduction — the krácený-odpočet shape, +60 deductible and +40 not —
        has two, and ř. 47 asks for the acquisition "v plné výši", the full
        value. Taking ``[:1]`` would file 60 % of an asset's tax and nothing
        would disagree with it.

        ⚠️ **18.0 difference.** The tag is resolved per DOCUMENT TYPE, because
        this chart signs its tag names and the sign is the side's: ``+VAT 47
        Total`` on the invoice repartition, ``-VAT 47 Total`` (carrying
        ``tax_negate``) on the refund one.

        This module's own engine would not notice if that were wrong — a
        negative control proved it. ``_eval_tags`` resolves a term through
        ``_get_tax_tags``, which matches BOTH signed variants, and sums the
        raw balance, so a credit note's +100 leg reads negative and reduces
        ř. 47 whichever of the two tags it carries. The figures come out right
        either way, which is exactly why the sign needs a test of its own.

        It matters to everything ELSE that reads these tags. Odoo's own tax
        report multiplies by ``tax_negate``
        (``account_reports/models/account_report.py``, ``CASE WHEN
        acc_tag.tax_negate THEN -1 ELSE 1 END``), so an unsigned tag on a
        refund leg inverts ř. 47 there; and CE's ``account.report`` treats the
        ± pair as structural, sorting a line's tags by ``tax_negate``. A tag
        that does not follow the chart's convention is a tag that only our
        reader can read.

        Idempotent: a line already carrying its tag is left alone.
        """
        self.ensure_one()
        touched = 0
        for document_type, reps in (
            ("invoice", tax.invoice_repartition_line_ids),
            ("refund", tax.refund_repartition_line_ids),
        ):
            base_tag = self._cz_deduction_tag("47", "Base", document_type)
            total_tag = self._cz_deduction_tag("47", "Total", document_type)
            base = reps.filtered(lambda r: r.repartition_type == "base")
            legs = reps.filtered(
                lambda r: r.repartition_type == "tax" and r.factor_percent > 0)
            for lines, tag in ((base, base_tag), (legs, total_tag)):
                for rep in lines:
                    if tag not in rep.tag_ids:
                        rep.tag_ids = [(4, tag.id)]
                        touched += 1
        return touched

    def _cz_create_asset_acquisition_taxes(self):
        """Create (or adopt) the ``Majetek`` purchase taxes. Idempotent.

        ř. 47 has been computable since this module shipped — `l10n_cz`
        declares ``VAT 47 Base`` and ``VAT 47 Total`` in its tax report, and
        ``nar_maj``/``od_maj`` read them — and **no shipped tax carries
        either**, so the row filed 0.00 whatever the taxpayer bought.

        The missing fact is per-document and binary: whether a purchase is
        dlouhodobý majetek. Odoo has nowhere to put it — the asset models are
        downstream of the bill, and the VAT return is computed from
        repartition tags, which are a property of the TAX. So the tax is where
        it goes, exactly as the legacy systems this migrates from do it:
        Vario's tax position table has "Majetek", "EU Majetek" and
        "TZ Majetek" beside its ordinary positions, and Pohoda the same.

        A twin is a ``copy()`` of its source, so the rate, the repartition
        shape, the accounts and the ř43/44 deduction tags are the source's by
        construction rather than by restatement — which is what keeps the two
        from drifting when the chart changes.

        **This chart yields 14 twins, not 19.0's 16**: 18.0 ships the domestic
        rates as plain ``21%`` and ``12%`` where 19.0 splits them into
        ``21% G``/``21% S``/``12% G``/``12% S``. So the domestic twins are
        ``21% Majetek`` and ``12% Majetek``, and anything mapping legacy tax
        positions onto them has to read the name off this series rather than
        assume 19.0's.

        **And there is no fiscal-position rewiring here, because there is
        nothing to rewire.** 19.0 carries the replacement on the tax
        (``original_tax_ids`` / ``replacing_tax_ids``), where a copy inherits
        it and the Intra-Community position would otherwise map one domestic
        line onto both the plain EU tax and its twin — self-assessing the
        acquisition twice. 18.0 has neither field: mapping lives in
        ``account.fiscal.position.tax`` rows, which a ``copy()`` of the tax
        does not touch, and this module deliberately does not build the
        intra-Community mapping on this series at all. The consequence is that
        an EU asset purchase has to be entered with ``21% EU G Majetek``
        directly; the position will not reach it from ``21% Majetek``.

        Runs on install, on chart load and from a migration, and
        ``_cssk_create_historic_vat_taxes`` is called **after** it so the twins
        acquire their own historical rates. Safe to re-run: a tax already
        carrying the name this would generate is adopted — stamped and
        re-tagged — rather than duplicated.
        """
        # Memoise the signed/unsigned answer for the whole run, the way
        # _cz_tag_selfassessed_deduction does: _cz_deduction_tag asks per tag
        # per document type otherwise, which is four queries per twin.
        self = self.with_context(cz_signed_tags={})
        Tax = self.env["account.tax"].with_context(active_test=False)
        total = 0
        for company in self:
            if company.chart_template != "cz":
                continue
            # ⚠️ Per company. Hoisted out of this loop, the second company
            # logs the first one's changes as its own.
            created = adopted = tagged = 0
            sources = Tax.search([
                ("company_id", "=", company.id),
                ("type_tax_use", "=", "purchase"),
                # Current rates only. The historical clones are made FROM the
                # twins afterwards; twinning a clone as well would produce two
                # records for one concept, each named for one half of the other.
                ("cssk_historic_valid_from", "=", False),
                # Never twin a twin: "21% Majetek Majetek".
                ("cz_asset_source_tax_id", "=", False),
            ])
            for source in sources:
                # A tax the chart has already replaced is history; see
                # _cssk_tax_is_superseded.
                if company._cssk_tax_is_superseded(source):
                    continue
                names = {
                    _cz_tag_key(t.name)
                    for t in source.invoice_repartition_line_ids.filtered(
                        lambda r: r.repartition_type == "base").tag_ids
                }
                if not (names & CZ_ASSET_SOURCE_TAGS):
                    continue
                if source.amount_type == "group" or source.children_tax_ids:
                    # A group tax's children carry the repartition, and
                    # ``copy()`` points the twin at the ORIGINAL children — so
                    # the twin would apply the untwinned children and reach
                    # ř. 47 on none of them. `l10n_cz` ships no such purchase
                    # tax; a user who builds one gets a warning rather than a
                    # twin that silently reports nothing.
                    _logger.warning(
                        "l10n_cz_vat_return: %s is a group tax, so no ř47 twin "
                        "was made — its children would have to be twinned "
                        "first", source.name,
                    )
                    continue
                # ⚠️ Found by the FIELD, not by the name. ``name`` is
                # translatable and the chart ships ``name@cs``, so
                # ``source.name`` reads "21 %" under cs_CZ and "21%" under
                # en_US: a name-keyed lookup finds nothing on the second
                # language and creates a duplicate twin for every tax.
                existing = Tax.search([
                    ("company_id", "=", company.id),
                    ("cz_asset_source_tax_id", "=", source.id),
                    ("cssk_historic_valid_from", "=", False),
                ], limit=1)
                name = "%s %s" % (source.name, CZ_ASSET_SUFFIX)
                if not existing:
                    # Nothing of ours yet. A tax somebody made by hand under
                    # the name this would generate is adopted instead of
                    # duplicated — the same courtesy the historical-rate
                    # generator extends.
                    #
                    # ⚠️ Keyed on exactly what ``_constrains_name`` is keyed
                    # on — company root, name, type_tax_use, tax_scope and
                    # country_id. A narrower search adopts a tax the
                    # constraint does not consider a duplicate at all; a wider
                    # one leaves a real collision unseen, and then ``copy()``
                    # raises "Tax names must be unique!" and takes the whole
                    # chart load or upgrade down with it.
                    taken = Tax.search([
                        ("company_id", "child_of", company.root_id.id),
                        ("name", "=", name),
                        ("type_tax_use", "=", source.type_tax_use),
                        ("tax_scope", "=", source.tax_scope),
                        ("country_id", "=", source.country_id.id),
                    ])
                    free = taken.filtered(
                        lambda t: not t.cz_asset_source_tax_id)[:1]
                    if free:
                        existing = free
                    elif taken:
                        _logger.warning(
                            "l10n_cz_vat_return: %s is already the ř47 twin of "
                            "%s, so %s has none — rename one of them",
                            taken[0].name,
                            taken[0].cz_asset_source_tax_id.name, source.name,
                        )
                        continue
                if existing:
                    existing.cz_asset_source_tax_id = source.id
                    adopted += 1
                else:
                    existing = source.copy({
                        "name": name,
                        "cz_asset_source_tax_id": source.id,
                    })
                    company._cz_suffix_every_translation(source, existing)
                    created += 1
                tagged += company._cz_asset_acquisition_tag_legs(existing)
            total += created + adopted
            if created or adopted:
                _logger.info(
                    "l10n_cz_vat_return: %s asset-acquisition tax(es) created, "
                    "%s adopted, %s ř47 tag(s) placed on %s",
                    created, adopted, tagged, company.display_name,
                )
        return total

    def _cz_asset_acquisition_taxes(self):
        """Every ``Majetek`` tax of these companies, archived ones included."""
        return self.env["account.tax"].with_context(active_test=False).search([
            ("company_id", "in", self.ids),
            ("cz_asset_source_tax_id", "!=", False),
        ])
