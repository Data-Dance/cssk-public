from odoo import _, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _cssk_statutory_footprint(self):
        """Which VAT-return rows this posting feeds.

        Read through ``_iter_tag_terms`` — the grammar's ONE parser — and not
        with a reader of its own. The formula is multi-term (``09|09a|09b``,
        and a term may carry its own sign), so asking ``_get_tax_tags`` for the
        whole string looked for a tag literally named ``09|09a|09b``, found
        none, and the row never appeared in any document's footprint. 55 of the
        158 Slovak line definitions are multi-term, including the ones that
        matter most: the § 69 reverse charge split by rate, ``18|18a``, and the
        § 25 both-sides case ``-24|+24_PR``. A posting on a Slovak
        reverse-charge supply reported no DPH row at all — while the same
        posting's control-statement and financial-statement rows reported
        correctly, so the footprint looked like it was working.

        That parser's own docstring already said why: "ONE parser for the
        grammar, because two read it… They had drifted". This was a third
        reader.

        A term's SIGN says how the row consumes the line, not whether it does,
        so reachability unions the terms and ignores the signs.
        """
        res = super()._cssk_statutory_footprint()
        if not self.tax_tag_ids:
            return res
        country = self._cssk_footprint_country()
        defs = self.env["cssk.vat.return.line.def"].search(
            [("kind", "=", "tags")] + self._cssk_footprint_version_domain())
        Tag = self.env["account.account.tag"]
        parser = self.env["cssk.vat.return"]
        seen = set()
        for ldef in defs:
            if ldef.code in seen:
                continue
            tags = Tag.browse()
            for _term_sign, term in parser._iter_tag_terms(ldef.tag_formula):
                tags |= Tag._get_tax_tags(term, country.id)
            if tags & self.tax_tag_ids:
                seen.add(ldef.code)
                res.append({"form": _("VAT return (DPH)"), "code": ldef.code,
                            "name": ldef.name,
                            "res_model": "cssk.vat.return"})
        return res
