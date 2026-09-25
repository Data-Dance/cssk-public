# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
"""The provider a Slovak company should have, created for it.

Installing a provider module adds SERVICE OPTIONS to a selection; it does not
create a provider. Nothing in the OCA ``currency_rate_update`` family ships a
provider record — not the base module, not this one, not the Czech one — so the
provider list is empty after install and stays empty until somebody notices and
fills the form in. That reads as a broken module rather than as a configuration
step, and the configuration is not really a choice: for a Slovak company the
ECB reference rate IS the statutory rate (NBS publishes it), the interval is
daily, and non-publishing days have to be filled or a weekend invoice has no
rate to value against.

WHAT THIS DELIBERATELY DOES NOT DO is decide which currencies a company trades
in. It configures the ones the database already has active — a currency nobody
has enabled is not one this company deals in, and activating currencies to make
a provider look complete would put rates, and therefore revaluation, on books
that never asked for them. A company with no active foreign currency gets no
provider, because there would be nothing for it to fetch.

It is idempotent and it never touches a provider that already exists. Re-running
it is safe, which matters: ``post_init_hook`` fires once, and the common case
for "the list is still empty" is a database where the foreign currency was
activated afterwards. The server action in ``data/`` is the re-run.
"""

import logging

from odoo import Command, _, api, models

_logger = logging.getLogger(__name__)

#: For a Slovak company this is not a preference. Národná banka Slovenska
#: publishes the ECB reference rate as the rate for the day, so the ECB service
#: is the statutory source and any other choice is a commercial rate used for
#: something else.
SK_DEFAULT_SERVICE = "ECB"


class ResCurrencyRateProvider(models.Model):
    _inherit = "res.currency.rate.provider"

    @api.model
    def _sk_default_provider_companies(self, companies=None):
        """Companies that file in Slovakia and so want the statutory provider.

        MATCHES ON EITHER COUNTRY, and that is not laziness. The first version
        read ``account_fiscal_country_id or country_id``, which looks like a
        fallback and is not one: ``compute_account_tax_fiscal_country`` fills
        the fiscal country only WHEN IT IS EMPTY and never re-syncs it, so a
        database created from the US-defaulted template and then made Slovak
        keeps ``account_fiscal_country_id = US`` for ever. The ``or`` therefore
        sees a stale value as present and the fallback can never fire —
        precisely on the databases that need it. It created zero providers on a
        company whose ``country_id`` was SK.

        Either field naming Slovakia is taken as meaning the company files
        there. A false positive is a provider somebody archives in one click; a
        false negative is silence, which is what this cost.
        """
        target = self.env.ref("base.sk", raise_if_not_found=False)
        if not target:
            return self.env["res.company"].browse()
        if companies is None:
            companies = self.env["res.company"].search([])

        def files_there(company):
            countries = company.country_id
            # ``account`` need not be installed — this module does not depend
            # on it and must not start doing so for a default.
            if "account_fiscal_country_id" in company._fields:
                countries |= company.account_fiscal_country_id
            return target in countries

        return companies.filtered(files_there)

    @api.model
    def _sk_default_provider_currencies(self, company):
        """What this company actually deals in, of what the service offers.

        ⚠️ DO NOT read ``available_currency_ids`` off a ``new()`` record to get
        this. That was the first version and it silently included the company's
        own currency: ``convert_to_cache`` for an x2many on an in-memory record
        rewrites the ids as ``NewId(...)`` ("x2many field value of new record
        is new records"), so ``currency != company.currency_id`` compared
        ``NewId(126)`` against ``126`` and was TRUE for every row — the filter
        removed nothing and the provider was created quoting EUR against EUR.
        It took a live test run to see it; nothing about the code reads wrong.

        ``_get_supported_currencies`` returns plain strings, so asking it on a
        throwaway record is safe, and the search that follows returns real
        records — with ``active_test`` applied, which is where the "already
        active" restriction actually comes from.
        """
        supported = self.new({"service": SK_DEFAULT_SERVICE})\
            ._get_supported_currencies()
        if not supported:
            return self.env["res.currency"].browse()
        return self.env["res.currency"].search([
            ("name", "in", list(supported)),
            ("id", "!=", company.currency_id.id),
        ])

    @api.model
    def _sk_ensure_default_provider(self, companies=None):
        """Create the statutory provider for any Slovak company lacking one.

        Returns what it created, so a caller can say so. Creating nothing is a
        normal outcome and not an error.
        """
        created = self.browse()
        for company in self._sk_default_provider_companies(companies):
            # ``sudo`` AND ``active_test=False``, and both matter.
            #
            # ARCHIVED: a provider somebody archived is a decision, and quietly
            # creating a live one beside it would reverse that without saying so.
            #
            # SUDO: ``currency_rate_update`` puts a multi-company record rule on
            # this model (``company_id in company_ids``). Without sudo the
            # existence check is filtered by that rule, so a user whose allowed
            # companies do not include this one sees no provider, concludes
            # there is none, and creates a SECOND — which the same rule then
            # hides from them. The check has to see what is really there even
            # though the caller may not. Creation stays unprivileged, and the
            # company list below is already whatever the caller can see, so
            # this reads more than it may write and escalates nothing.
            if self.sudo().with_context(active_test=False).search_count(
                    [("company_id", "=", company.id),
                     ("service", "=", SK_DEFAULT_SERVICE)]):
                continue
            currencies = self._sk_default_provider_currencies(company)
            if not currencies:
                _logger.info(
                    "currency_rate_update_sk: %s has no active foreign "
                    "currency the ECB publishes, so no provider was created.",
                    company.display_name)
                continue
            vals = {
                "company_id": company.id,
                "service": SK_DEFAULT_SERVICE,
                "currency_ids": [Command.set(currencies.ids)],
                "interval_type": "days",
                "interval_number": 1,
            }
            # Set only if this database has the field — it is added by THIS
            # module, but this same shape is used by the Czech one, where it
            # is present only when both are installed.
            if "fill_missing_days" in self._fields:
                vals["fill_missing_days"] = True
            created |= self.create(vals)
            _logger.info(
                "currency_rate_update_sk: created the ECB provider for %s "
                "with %d currenc(ies).", company.display_name, len(currencies))
        return created

    @api.model
    def action_sk_ensure_default_provider(self):
        """The re-run, from the provider list's action menu.

        The rights check is here and not on the action because Odoo 19 has no
        ``groups_id`` on ``ir.actions`` — it was removed, and writing one into
        the XML fails the module's own data load. So the action is visible to
        everybody who can see the provider list, which by ``currency_rate_update``'s
        ACL includes the Accounting Manager, who has READ and nothing else. Left
        unguarded that is a button which can only ever raise AccessError; a
        sentence saying who can do it is a better answer than a traceback.
        """
        if not self.has_access("create"):
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "message": _(
                        "Creating a rate provider needs Settings access. Ask "
                        "an administrator to run this."),
                    "type": "warning",
                },
            }
        created = self._sk_ensure_default_provider()
        if created:
            message = _("Created %s provider(s).", len(created))
        else:
            message = _(
                "Nothing to create: every Slovak company already has an ECB "
                "provider, or has no active foreign currency to fetch.")
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "message": message,
                "type": "success" if created else "info",
                # Reload, not close: the caller is LOOKING at the provider
                # list and the whole point of the action is that it now has
                # rows in it. A toast saying "created 1" over an unchanged
                # empty list reads as a failure.
                "next": {"type": "ir.actions.client", "tag": "reload"},
            },
        }
