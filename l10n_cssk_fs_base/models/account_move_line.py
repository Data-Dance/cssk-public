from odoo import _, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _fs_form_label(self, kind):
        return {
            "balance_sheet": _("Balance sheet"),
            "profit_loss": _("Income statement"),
            "cash_flow": _("Cash flow statement"),
            "equity_changes": _("Statement of changes in equity"),
        }.get(kind, _("Financial statements"))

    def _cssk_statutory_footprint(self):
        """Which financial-statement rows this posting feeds.

        Driven through the SAME matcher the statement computes with, which is
        the whole point of the reverse direction: an answer that disagrees
        with the figures is worse than no answer. It had quietly forked — a
        local ``re.findall(r"[0-9]+")`` plus ``startswith`` — and that fork
        was wrong twice:

        * it read only ``account_formula``, so an account named ONLY in a
          row's KOREKCIA column reported no row at all. 51 UZPODv14 rows carry
          one, and 073000 (oprávky k softvéru) appears in that version once as
          a correction and never as a base formula — so posting software
          depreciation answered "this feeds nothing", when it feeds r005's
          korekcia column.
        * ``02X`` means "any account of group 02 that no row names", and
          reducing it to the bare prefix ``02`` claimed every 02x account for
          the residual row — including ones another row names outright, which
          the evaluator would never absorb there.
        """
        res = super()._cssk_statutory_footprint()
        code = self.account_id.code or ""
        if not code:
            return res
        # The statements read an account under the code it is REPORTED as
        # (``cssk.statement.account.map``), so the reverse direction must too.
        # A debit- or credit-only mapping depends on the balance at the period
        # end, which one posting does not decide: offer both codes and say so.
        sides = self.env["cssk.statement.account.map"]._cssk_map_for(
            self.company_id).get(self.account_id.id, {})
        if "any" in sides:
            candidates = [(sides["any"], False)]
        else:
            candidates = [(code, bool(sides))] + [
                (alt, True) for alt in sides.values()]
        defs = self.env["cssk.fs.statement.line.def"].search(
            [("kind", "in", ["accounts", "accounts_open", "accounts_close"])]
            + self._cssk_footprint_version_domain())
        matcher = self.env["cssk.fs.statement"]
        claimed_by_version = {}
        seen = set()
        for ldef in defs:
            version = ldef.version_id
            if version.id not in claimed_by_version:
                claimed_by_version[version.id] = (
                    version._cssk_claimed_codes(),
                    version._cssk_two_sided_prefixes(),
                    version._cssk_tag_codes(),
                )
            claimed, two_sided, tag_codes = claimed_by_version[version.id]
            column, side_dependent = None, False
            for candidate, by_side in candidates:
                column = self._fs_matching_column(
                    ldef, candidate, matcher, claimed, version, tag_codes)
                if column:
                    side_dependent = by_side
                    break
            if not column:
                continue
            kind = version.statement_kind
            key = (kind, ldef.code, column)
            if key in seen:
                continue
            seen.add(key)
            name = ldef.name
            if column == "correction":
                name = _("%s — korekcia", name)
            if side_dependent or version._cssk_token_code_in(ldef, two_sided):
                # The account is on BOTH sides of this form and which row it
                # reaches depends on the sign of its balance, which a single
                # posting does not decide. Say so rather than pick.
                name = _("%s — side depends on the account's balance", name)
            res.append({"form": self._fs_form_label(kind),
                        "code": ldef.code, "name": name,
                        "res_model": "cssk.fs.statement"})
        return res

    @staticmethod
    def _fs_matching_column(ldef, code, matcher, claimed, version, tag_codes):
        """``'base'`` / ``'correction'`` / ``None`` — which column claims it.

        A row can name an account in either, and the two mean different
        things on the filed form: brutto against korekcia.

        The token is split by the SAME parser the evaluator uses, and the tag
        filters are applied the same way, so the two directions cannot
        disagree. Reducing a token to its digits instead reported a posting on
        a 665 account as feeding all THREE IX rows — including the residual
        "ostatné" leaf, which by construction it does not reach.
        """
        for column, formula in (("base", ldef.account_formula),
                                ("correction", ldef.account_formula_correction)):
            for raw in (formula or "").split(","):
                _neg, prefix, include, exclude = matcher._cssk_split_token(
                    raw, tag_codes)
                if not prefix:
                    continue
                if include is not None and code not in include:
                    continue
                if code in exclude:
                    continue
                if matcher._cssk_code_matches(code, prefix, claimed):
                    return column
        return None
