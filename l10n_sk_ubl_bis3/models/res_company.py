# -*- coding: utf-8 -*-
from odoo import api, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.model_create_multi
    def create(self, vals_list):
        """Put a company created with its DIČ onto ``0245`` + that DIČ.

        Core creates the company's partner from a fixed list of values —
        ``name``, ``vat``, ``country_id`` and a few more, never the DIČ — and
        flushes it, so ``peppol_eas`` is computed before the related
        ``l10n_sk_dic`` is written through. With an IČ DPH that yields
        ``9950:<IČ DPH>``; without one, core falls back to the first SK code,
        which is also ``9950``, with no endpoint at all. When the DIČ arrives a
        moment later, ``9950`` is a valid SK code and the compute treats it as
        chosen, so one save on the company form leaves the partner on a scheme
        nobody picked, while the same values on a contact give ``0245``.

        Only partners core created here are moved. A ``partner_id`` passed in
        is an existing contact, and its scheme may well be a decision.
        """
        # EXTENDS 'base'
        # core's own test for creating the partner, verbatim
        created_partner = [
            bool(vals.get('name') and not vals.get('partner_id'))
            for vals in vals_list
        ]
        companies = super().create(vals_list)
        partners = self.env['res.partner'].concat(*(
            company.partner_id
            for company, created in zip(companies, created_partner)
            if created
        ))
        partners.action_l10n_sk_adopt_dic_participant()
        return companies
