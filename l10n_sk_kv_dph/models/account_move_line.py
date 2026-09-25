from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _cssk_resolve_section_code(self):
        """SK KV DPH section resolver (line level).

        Returns a *natural* section code; the below/above-threshold split for
        simplified invoices (B.3.1 vs B.3.2) is decided at populate time, so
        simplified received lines are tagged ``B.3`` here.

        Order matters — **reverse charge is checked first**. Outbound intra-EU
        supplies (§ 43) are excluded (they belong to the EC sales list, not the
        KV). Inbound self-assessed supplies — foreign services (§ 69 ods. 2) and
        intra-EU goods acquisitions (§ 11) — DO belong in B.1 per the KVDPHv17
        poučenie (see the inbound branch).

        NOTE: best-effort decision tree — must be validated by a SK accountant,
        in particular: the §69 ods. 12 domestic-reverse-charge goods list and
        e-kasa (D.1). Supplies to non-taxable persons (D.2), domestic or EU,
        were confirmed by an accountant on 2026-09-21.
        """
        res = super()._cssk_resolve_section_code()
        if res:
            return res

        company = self.company_id
        if company.account_fiscal_country_id.code != "SK":
            return False
        taxes = self._cssk_taxes()
        if self.parent_state != "posted" or not taxes:
            return False
        if self.tax_line_id:  # this is a tax line, not a base line
            return False

        # The invoice a cash-basis entry settles, not the entry: it has the
        # type, the partner and the flags; the entry has only the timing.
        move = self.move_id._cssk_vat_document()
        is_outbound = move.move_type in ("out_invoice", "out_refund")
        is_inbound = move.move_type in ("in_invoice", "in_refund")
        if not (is_outbound or is_inbound):
            # A journal entry can still report VAT. A self-assessed acquisition
            # is recorded as an internal document rather than a bill, and so
            # are manual corrections; skipping every non-invoice move drops
            # them out of the statement silently. Where the move type cannot
            # give the direction, the taxes can, provided they all point the
            # same way (a mixed entry is ambiguous and left alone).
            #
            # The decision tree below then classifies as usual — in particular
            # an intra-EU acquisition still reaches B.1 through the
            # reverse-charge branch, and a non-reverse-charge EU line is still
            # excluded from KV DPH.
            uses = set(taxes.mapped("type_tax_use"))
            is_outbound = uses == {"sale"}
            is_inbound = uses == {"purchase"}
            if not (is_outbound or is_inbound):
                return False

        # DECLARED first, derived second. An imported credit note is often
        # posted as a journal ENTRY — the Money import demotes 22 of them and
        # the i6 agenda is 16 926 entries against 4 invoices — and `entry` is
        # not one of the refund types, so a resolver that only reads
        # `move_type` sends every correction to A.1/B.2 and oddiel C.1 and C.2
        # can never be reached at all. Same reasoning as
        # `cssk_vat_direction` directly above it on the move.
        declared = move.cssk_vat_correction
        is_correction = (
            declared == "yes" if declared
            else move.move_type in ("out_refund", "in_refund")
        )
        is_reverse_charge = bool(
            taxes.filtered("cssk_control_is_reverse_charge")
        )
        is_eu = self._cssk_is_eu_counterparty()

        # Intra-EU supplies / acquisitions are not part of KV DPH.
        #
        # ⚠️ The exclusion tests the SUPPLY, not just the counterparty's
        # country, and the difference is not academic. "EU counterparty ⇒
        # intra-EU supply" holds only where the customer is VAT-registered in
        # another member state: a § 43 supply is exempt with credit precisely
        # because the acquirer self-assesses. Supply to a non-taxable EU
        # person and the place of supply is Slovakia, Slovak VAT is charged,
        # and it is an ordinary domestic taxable supply that belongs in the
        # statement.
        #
        # So a line BEARING Slovak VAT is not an intra-EU supply, whatever the
        # partner's country says. This is the converse of the rate test on A.1
        # below — that one excludes an exempt supply from a section meant for
        # taxable ones, this one stops a taxable supply being excluded as
        # though it were exempt — and it uses the same helper deliberately.
        #
        # Found by the MRP extractor on a Czech customer with no VAT number,
        # in both years: 450.00 base + 90.00 VAT in 2024-09 and 100.00 + 23.00
        # in 2025-08, both filed by the accountant in A.1, both reaching
        # r03/r04 on the return correctly and vanishing from KV DPH entirely.
        # 550.00 of taxed base that reached the return and no section at all.
        #
        # Which section it then takes is decided below with every other
        # domestic taxable supply: D.2 for a customer who is not a taxable
        # person (as that one was), A.1 otherwise. What is not in doubt is
        # that returning False here was wrong.
        if is_eu and not is_reverse_charge and not self._cssk_bears_vat():
            return False

        if is_correction:
            # C.1 corrects what A.1 reported, so it inherits A.1's exclusion:
            # a supply bearing no tax is not a taxable supply, and a correction
            # of one is not a correction to report. Without this the branch was
            # an unguarded catch-all in the same way A.1 was before its own
            # rate test — and the two are not symmetric by accident, they
            # report the same population.
            #
            # Measured on the i6 agenda: C.1 produced 138 rows against 38
            # filed, and **97 of the 100 extra were zero-rated**, none of them
            # reverse-charge. The rate test accounts for essentially the whole
            # over-production.
            #
            # Deliberately NOT applied to C.2. It corrects what B.2 reported,
            # and B.2 has no rate test — so adding one here would break the
            # symmetry rather than complete it. C.2 over-produces too, but on
            # ordinary RATED credit notes (49 of 53 at 20 %), which is a
            # different question: which received credit notes are § 25
            # corrections for KV purposes at all. That needs a statutory
            # answer, not a rate test, and guessing it here would silently
            # drop real corrections.
            #
            # ⚠️ AND WHATEVER THAT ANSWER TURNS OUT TO BE, DO NOT NARROW C.2
            # BY REQUIRING THAT THE ORIGINAL WAS REPORTED IN B.2. That is the
            # obvious-looking way to cut the over-production and it is wrong.
            # Measured across 134 filed control statements of a Slovak s.r.o.
            # (PREMIER import, session fa4-24): of 11 filed C.2 rows, each
            # naming both the corrective document and the invoice it corrects,
            # **4 correct an original that appears in no filed B.2 anywhere** —
            # two suppliers with not a single B.2 row in any statement. The
            # likeliest reading is that those originals sat inside the B.3.1
            # aggregate, which carries no document numbers at all, so the
            # original cannot be matched even in principle.
            #
            # So C.2 membership follows from the correction being a § 25
            # oprava, not from the corrected document having been individually
            # reported. Conditioning on a matching B.2 would have dropped 4 of
            # those 11.
            #
            # (Same agenda: all 11 correct downward, and on 7 of them the
            # deducted part of the difference is smaller than the difference —
            # a koeficient partial deduction on the original. Neither fact is
            # acted on here; recorded because the next person to open this
            # question will want to know the population is not uniform.)
            if is_outbound and not self._cssk_bears_vat():
                return False
            return "C.1" if is_outbound else "C.2"

        if is_outbound:
            # A.2 — domestic reverse charge supplied (supplier applies 0 %,
            # customer self-assesses, §69 ods. 12).
            if is_reverse_charge:
                return "A.2"
            # A.1 — standard domestic taxable supply **with VAT**.
            #
            # The rate test is load-bearing and this used to be an unguarded
            # catch-all. The poučenie limits A.1 to a supply on which a tax
            # liability arose under § 19, "okrem dodania, ktoré je oslobodené
            # od dane" — so a supply exempt from tax does not belong here at
            # all. An export under § 47 to a NON-EU customer is exactly that:
            # it is zero-rated, and it passes the intra-EU exclusion above
            # because the counterparty is not in the EU, so it fell straight
            # into a section meant for domestic taxable supplies.
            #
            # Found by the i6 extractor on real data: December 2024 put four
            # `0% EXP` lines carrying 97 999 of base into A.1. The export
            # belongs on the return (r15/r16) and nowhere in KV DPH.
            #
            # Deliberately NOT applied to A.2 above: a domestic reverse charge
            # under § 69 ods. 12 is zero-rated *by construction* — the supplier
            # applies no tax and the customer self-assesses — so testing the
            # rate there would empty the section that exists to report it.
            if not self._cssk_bears_vat():
                return False
            # D.2 — the same supply to a customer who is NOT a taxable person.
            #
            # A.1 reports "údaje z vyhotovenej faktúry"; D.2 (§ 78a ods. 2
            # písm. d) is the aggregate for domestic taxable supplies the
            # platiteľ was not obliged to invoice at all — § 72 obliges an
            # invoice towards a zdaniteľná osoba or a právnická osoba, and a
            # private individual is neither.
            #
            # ⚠️ THE TEST IS THE IČO, NOT THE IČ DPH, and getting that backwards
            # breaks more than it fixes. A Slovak neplatiteľ business — a
            # živnostník or s.r.o. under the registration threshold — holds no
            # IČ DPH and IS a zdaniteľná osoba, so § 72 applies and it belongs
            # in A.1 with ``Odb`` simply omitted. That is legal: A1/@Odb is
            # ``use="optional"`` in every vzor we ship (2014, 2016, 2023, 2025);
            # only A2/@Odb is required.
            #
            # Measured on a Slovak s.r.o.'s 2016–2019 agenda against the 32
            # control statements the company actually filed (PREMIER import,
            # session fa4-24). Our computed A.1 splits three ways:
            #
            #     has IČ DPH               86 moves   18 835.98   filed A.1
            #     IČO, no IČ DPH            3 moves      148.62   filed A.1
            #     natural person, neither   5 moves      731.48   filed D.2
            #
            # 18 835.98 + 148.62 is the filed A.1 total to the cent, and the
            # 731.48 is the filed D.2 total to the cent in each of its four
            # periods. The accountant also filed 3 of the 86 A.1 rows with no
            # customer IČ DPH at all, which is the same point from the other
            # side: A.1 without an IČ DPH is normal, A.1 without an IČO is not.
            #
            # Verified after the change on that same agenda: A.1 18 984.60,
            # B.3.1 5 535.93 and D.2 731.48 all equal the filed figures
            # exactly, 92 of 95 section-periods agree, and the entire residual
            # is two documents that are not a code question — one where the
            # source's ledger claims an input deduction its own VAT return does
            # not (200.00), and one § 69 ods. 3 service the source filed in A.2
            # where this resolver says B.1 (∓59.00).
            #
            # Still open, and asked of that accountant: all five were issued as
            # ordinary faktúry (PREMIER book `OF`, invoice numbers), not
            # pokladničné doklady — so on this agenda a VOLUNTARILY issued
            # invoice to a private individual still went to D.2, i.e. the
            # customer decides and not the invoice obligation. One agenda.
            #
            # WHATEVER THE CUSTOMER'S COUNTRY. This used to read `not is_eu
            # and ...`, sending a private person from another member state to
            # A.1 — which is what the MRP agenda's accountant filed for a
            # Czech private customer taxed at Slovak rates (2024-09, 2025-08).
            # Asked directly on 2026-09-21, a second Slovak accountant
            # (Atheo) answered without qualification: "Fyzické osoby
            # nepodnikatelia idú do D2." That is also the statutory reading:
            # § 72 obliges an invoice towards a zdaniteľná osoba or a
            # právnická osoba, and a private individual in Brno is neither,
            # exactly as one in Bratislava is not. The MRP filing is the
            # outlier, not the rule. (An EU customer who IS VAT-registered
            # never gets here — the supply is zero-rated and excluded above.)
            if not self._cssk_customer_is_taxable_person():
                return "D.2"
            return "A.1"

        # inbound
        # B.1 — received supplies where the recipient is liable for the tax in
        # tuzemsko under § 69 ods. 2, 3, 6, 7, 9 až 12 (KVDPHv17 poučenie, oddiel
        # B.1). This is NOT limited to domestic § 69 ods. 12 — it explicitly
        # covers self-assessed FOREIGN services (§ 15 ods. 1 dodané zahraničnou
        # osobou, i.e. § 69 ods. 2) and intra-EU goods acquisitions (§ 11/§ 11a).
        # Confirmed by the SK accountant against the official poučenie (only
        # exempt foreign services are excluded, handled upstream by the tax/tag).
        if is_reverse_charge:
            return "B.1"
        # B.2 and B.3 report the tax the recipient DEDUCTS ("ak príjemca
        # uplatňuje odpočítanie dane"), so a received supply bearing no tax has
        # nothing to report there: an exempt supply (insurance, a § 28-§ 42
        # service), a customs line carrying duty only, a 0 % purchase tax. It
        # is the rate test of A.1 on the received side, and the same helper.
        #
        # Reported by an external accountant: a 0 % purchase tax reached B.2
        # as a row with D="0.00", which FS SR does not accept.
        #
        # Deliberately after B.1 — a self-assessed supply is zero-rated on the
        # supplier's document by construction — and NOT applied to C.2, for
        # the reasons given on the correction branch above.
        if not self._cssk_bears_vat():
            return False
        # B.3 — simplified invoice / receipt (split B.3.1/B.3.2 at populate).
        if move.l10n_sk_kv_is_simplified:
            return "B.3"
        # ⚠️ A received document with NO COUNTERPARTY AT ALL is a simplified
        # invoice whether or not anything flagged it as one, because oddiel B.2
        # reports the supplier's IČ DPH per row — a B.2 row without a
        # counterparty cannot exist. That is a property of the FORM rather than
        # a guess about the document, which is what makes it safe to derive
        # here instead of waiting for an extractor to set the flag.
        #
        # The flag stays the primary test: an importer that knows a document is
        # simplified should say so, and one that knows the supplier should
        # record it. This catches the case where neither happened, which is the
        # ledger-built receipt.
        #
        # Found by EXPORTING rather than by comparing. On the MRP agenda 49
        # ledger receipts classified B.2, and the totals agreed with the filing
        # to the cent — the accountant filed them as a B.3 aggregate of
        # 2 113.25 and the comparison matched it, so the section difference
        # read as presentational. It is not: the export failed with "B.2 row(s)
        # without the counterparty's IČ DPH", and no placeholder could fix it
        # because there was no counterparty to give one to. Reclassified, both
        # months exported cleanly. The difference is between a filable and an
        # unfilable statement, and only the export path could show it.
        if not move.partner_id:
            return "B.3"
        # B.2 — standard received invoice with input VAT deduction.
        return "B.2"

    def _cssk_customer_is_taxable_person(self):
        """Best available answer to "is the customer a zdaniteľná osoba?".

        Odoo stores no such field, so this is a proxy and is documented as
        one: an IČ DPH or an IČO (``company_registry``) means a business, and
        a partner carrying neither — or no partner at all — is treated as a
        private individual. ``is_company`` is deliberately NOT consulted: a
        Slovak živnostník is a natural person in Odoo's sense and a taxable
        person in the statute's, and keying on it would misfile every one.

        ⚠️ THIS DEPENDS ON THE IČO ACTUALLY BEING RECORDED, and until
        ``l10n_cssk_core`` 7babaf6 (2026-09-08) it could not be: core hides
        ``company_registry`` behind ``invisible="parent_id or not is_company"``,
        so on a CZ/SK partner stored as a natural person — which is what
        ``website_sale`` creates, and what a živnostník is — the field was
        invisible in the form. A database that predates that fix can hold
        unregistered BUSINESSES with an empty ``company_registry``, and this
        method reads those as private individuals and sends their supplies to
        D.2. Before trusting the split on an existing agenda, look for domestic
        customers with sales history and no IČO and fill the number in — the
        register lookup in ``l10n_sk_trade_registry`` can do it from the name.
        """
        self.ensure_one()
        partner = self.move_id._cssk_vat_document(
        ).partner_id.commercial_partner_id
        if not partner:
            return False
        return bool(partner.vat or partner.company_registry)

    def _cssk_bears_vat(self):
        """Whether this line actually carries Slovak VAT at a non-zero rate.

        Tested on the **rate**, not on a computed amount: the resolver runs
        before any amount is derived, and a zero-rated line is zero-rated
        whatever its base happens to be. A line whose only percent tax is at
        0 % — an export under § 47, an exempt supply under § 28 to § 42 — bears
        no tax, however large the supply.
        """
        self.ensure_one()
        return bool(self._cssk_taxes().filtered(
            lambda t: t.amount_type == "percent" and t.amount
        ))

    def _cssk_is_eu_counterparty(self):
        """Whether the counterparty is in another EU member state.

        Geography only — deliberately. Whether a supply to that counterparty is
        an intra-EU supply is a different question, because § 43 needs the
        acquirer to be VAT-registered there, and the caller answers it by also
        testing whether the line bears Slovak VAT. Keeping the two apart means
        neither has to guess at the other's evidence: this reads the partner,
        the caller reads the document.
        """
        self.ensure_one()
        country = self.move_id._cssk_vat_document().partner_id.country_id
        if not country or country.code == "SK":
            return False
        eu = self.env.ref("base.europe", raise_if_not_found=False)
        return bool(eu) and country in eu.country_ids
