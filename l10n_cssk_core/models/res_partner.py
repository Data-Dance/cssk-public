from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..tools import ICO_LENGTH, is_valid_ico, normalize_registry

#: The countries whose company registry is an IČO. The mod-11 check and the
#: eight-digit shape are identical in both; nowhere else does either apply.
REGISTRY_COUNTRIES = ("CZ", "SK")


class ResPartner(models.Model):
    _inherit = "res.partner"

    l10n_cssk_person_type_id = fields.Many2one(
        "cssk.person.type",
        string="Entity Type",
        help="Person / entity type of the partner. Drives statutory "
        "classification (e.g. control-statement section selection).",
    )

    # ------------------------------------------------------------------
    # Company registry (IČO)
    #
    # ``company_registry`` is core's field and core validates nothing in it.
    # On the Data Dance production base that left 12 of 96 CZ/SK values
    # unusable -- "Test", "12345", "-", "JUSTICE.CZ", and three cases of the
    # company NAME pasted into the number field, two of which reached posted
    # invoices. On a Czech invoice a company name in place of the IČO is a
    # defect in a statutory document, not untidy data.
    #
    # Storage is canonicalised and validity is enforced, both scoped to
    # CZ/SK. Scoping is not optional: a German supplier's "HRB 12345", a US EIN
    # "12-3456789" and a Latvian 11-digit registry are all legitimate, and an
    # unscoped check rejects every one of them.
    # ------------------------------------------------------------------

    def _l10n_cssk_uses_ico(self):
        """True when this partner's registry number should be an IČO.

        Keyed on the country and NOT on ``_deduce_country_code``, which also
        reads the VAT prefix. A foreign company VAT-registered in Czechia
        carries a ``CZ…`` VAT number while its company registry is still its
        home register's — a German ``HRB 12345`` — and deducing CZ there would
        reject a legitimate value. Core scopes the field's own uniqueness by
        country too. A partner whose country is not yet known is not checked;
        the constraint fires as soon as one is set.
        """
        self.ensure_one()
        return self.country_code in REGISTRY_COUNTRIES

    def _l10n_cssk_canonicalise_registry(self):
        """Rewrite ``company_registry`` to its canonical zero-padded form.

        Only ever rewrites a value that is ALREADY a valid IČO, so this
        cannot turn a typo into a different-looking typo, and the constraint
        below still reports exactly what the user typed. Runs after the write
        rather than on the incoming values because the country may itself be
        arriving in the same write, or be inherited from a parent.
        """
        for partner in self:
            current = partner.company_registry
            if not current or not partner._l10n_cssk_uses_ico():
                continue
            canonical = normalize_registry(current)
            if canonical != current and is_valid_ico(canonical):
                partner.with_context(
                    l10n_cssk_skip_registry_canon=True
                ).write({"company_registry": canonical})

    @api.model_create_multi
    def create(self, vals_list):
        partners = super().create(vals_list)
        partners._l10n_cssk_canonicalise_registry()
        return partners

    def write(self, vals):
        res = super().write(vals)
        if self.env.context.get("l10n_cssk_skip_registry_canon"):
            return res
        # ``parent_id`` matters because the registry is a commercial field and
        # the country an address one: re-parenting can change both without
        # either appearing in ``vals``.
        if {"company_registry", "country_id", "parent_id"} & vals.keys():
            self._l10n_cssk_canonicalise_registry()
        return res

    @api.constrains("company_registry", "country_id", "parent_id")
    def _check_l10n_cssk_company_registry(self):
        for partner in self:
            registry = partner.company_registry
            if not registry or not partner._l10n_cssk_uses_ico():
                continue
            if is_valid_ico(registry):
                continue
            # The registry is a commercial field, so a bad value on a parent
            # is synced onto every child and the constraint fires for those
            # too. Name the commercial entity the number actually belongs to;
            # naming whichever contact happened to be written first sends the
            # user to a record that has nothing to fix.
            owner = partner.commercial_partner_id or partner
            raise ValidationError(
                _(
                    "%(value)r is not a valid IČO for %(partner)s.\n\n"
                    "A Czech or Slovak company registry number is %(length)s "
                    "digits and carries a check digit; this one does not add "
                    "up. Please check it against the register — it is not the "
                    "company name, the VAT number or the Tax ID.",
                    value=registry,
                    partner=owner.display_name or _("this contact"),
                    length=ICO_LENGTH,
                )
            )

    @api.model
    def _get_company_registry_labels(self):
        """Call it what the customer calls it.

        Core returns ``{}`` and falls back to "Company ID" for every country;
        the l10n modules that care override this. Nothing did for CZ/SK, so
        the field carrying an IČO was labelled with a phrase no Czech or
        Slovak accountant uses.
        """
        labels = super()._get_company_registry_labels()
        labels.update({"CZ": _("IČO"), "SK": _("IČO")})
        return labels
