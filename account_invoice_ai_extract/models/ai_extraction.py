import base64
import json
import logging

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..tools.schema import EXTRACT_INVOICE_TOOL
from ..tools.prompt import EXTRACTION_PROMPT
from ..tools.resolver import normalize_vat, totals_consistent

_logger = logging.getLogger(__name__)


class AccountInvoiceAiExtraction(models.Model):
    _name = 'account.invoice.ai.extraction'
    _description = "AI Invoice Extraction"
    _inherit = ['mail.thread']
    _order = 'create_date desc'

    name = fields.Char(default='New', readonly=True, copy=False)
    company_id = fields.Many2one(
        'res.company', required=True, default=lambda s: s.env.company)
    attachment_id = fields.Many2one(
        'ir.attachment', string="Source PDF", required=True, ondelete='restrict')
    state = fields.Selection([
        ('pending', "Pending"),
        ('extracting', "Extracting"),
        ('extracted', "Extracted"),
        ('resolved', "Resolved"),
        ('needs_review', "Needs Review"),
        ('duplicate', "Duplicate"),
        ('error', "Error"),
    ], default='pending', tracking=True, index=True)
    raw_json = fields.Text(string="Model output", readonly=True)
    confidence = fields.Float(readonly=True, aggregator='avg')
    input_tokens = fields.Integer(string="Input tokens", readonly=True, help="Last run.")
    output_tokens = fields.Integer(string="Output tokens", readonly=True, help="Last run.")
    cost = fields.Float(string="Last Run Cost (USD)", readonly=True, digits=(12, 5))
    run_ids = fields.One2many(
        'account.invoice.ai.extraction.run', 'extraction_id', string="Runs", readonly=True)
    run_count = fields.Integer(compute='_compute_usage_totals', store=True)
    total_cost = fields.Float(
        string="Total Cost (USD)", compute='_compute_usage_totals', store=True,
        digits=(12, 5), aggregator='sum', help="Cumulative cost across all runs of this extraction.")
    partner_id = fields.Many2one('res.partner', readonly=True)
    move_id = fields.Many2one('account.move', string="Vendor Bill", readonly=True)
    error_message = fields.Text(readonly=True)
    provider_id = fields.Many2one(
        'muk_ai.provider', string="AI Provider Override",
        help="Force a specific provider for this extraction. Leave empty to use the "
             "company / default provider.")
    model_id = fields.Many2one(
        'muk_ai.model', string="AI Model Used", readonly=True,
        help="The provider model that actually ran this extraction.")

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'account.invoice.ai.extraction') or 'New'
        return super().create(vals_list)

    @api.depends('run_ids.cost')
    def _compute_usage_totals(self):
        for rec in self:
            rec.run_count = len(rec.run_ids)
            rec.total_cost = sum(rec.run_ids.mapped('cost'))

    # ------------------------------------------------------------------
    # Orchestration
    # ------------------------------------------------------------------
    def action_process(self):
        for rec in self:
            rec._process_one()
        return True

    def _process_one(self):
        self.ensure_one()
        try:
            self._run_extraction()
            if self.state == 'extracted':
                self._resolve()
        except Exception as error:  # noqa: BLE001 - surface, never crash the sweep
            _logger.exception("AI invoice extraction failed for %s", self.name)
            self.write({'state': 'error', 'error_message': str(error)})

    def _get_provider(self):
        self.ensure_one()
        return (
            self.provider_id
            or self.company_id.ai_extract_provider_id
            or self.env['muk_ai.provider']._get_default()
        )

    def _run_extraction(self):
        self.ensure_one()
        provider = self._get_provider()
        if not provider:
            raise UserError(_("No AI provider configured."))
        self.state = 'extracting'
        pdf = self.attachment_id
        block = {
            'type': 'muk_ai_attachment',
            'attachment_id': pdf.id,
            'filename': pdf.name,
            'mimetype': pdf.mimetype or 'application/pdf',
            'strategy': 'file',
            'data_b64': base64.b64encode(pdf.raw or b'').decode('ascii'),
        }
        inputs = [{'role': 'user', 'content': [{'text': EXTRACTION_PROMPT}, block]}]
        model = self.company_id.ai_extract_model_id.technical_name or None
        payload = provider._request_responses(
            inputs=inputs, tools_schema=[EXTRACT_INVOICE_TOOL], model=model)
        calls = payload.get('tool_calls') or []
        call = next((c for c in calls if c.get('name') == 'extract_invoice'), None)
        extraction = (call or {}).get('arguments')
        if not extraction:
            raise UserError(_("The model did not return an invoice extraction."))
        confidence = (extraction.get('classification') or {}).get('confidence') or 0.0
        usage = payload.get('usage') or {}
        model_rec = self.company_id.ai_extract_model_id or provider.default_model_id
        cost = model_rec._compute_usage_cost(usage)['total_cost'] if model_rec else 0.0
        input_tokens = int(usage.get('input_tokens') or 0)
        output_tokens = int(usage.get('output_tokens') or 0)
        self.env['account.invoice.ai.extraction.run'].create({
            'extraction_id': self.id,
            'provider_id': provider.id,
            'model_id': model_rec.id if model_rec else False,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'cost': cost,
            'confidence': confidence,
        })
        self.write({
            'raw_json': json.dumps(extraction, indent=2, ensure_ascii=False),
            'confidence': confidence,
            'model_id': model_rec.id if model_rec else False,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'cost': cost,
            'state': 'extracted',
        })
        self.message_post(body=_(
            "AI extraction complete — confidence %(conf).0f%%, %(in)s in / %(out)s out "
            "tokens, $%(cost).4f."
        ) % {'conf': confidence * 100, 'in': input_tokens, 'out': output_tokens, 'cost': cost})

    # ------------------------------------------------------------------
    # Deterministic resolution
    # ------------------------------------------------------------------
    @property
    def _extraction(self):
        return json.loads(self.raw_json) if self.raw_json else {}

    def _resolve(self):
        self.ensure_one()
        ex = self._extraction
        company = self.company_id

        ok, reason = totals_consistent(
            ex.get('totals'), ex.get('vat_breakdown'),
            tolerance=company.currency_id.rounding * 2 or 0.02)
        if not ok:
            return self._park_review(_("Totals failed reconciliation: %s") % reason)

        threshold = company.ai_extract_confidence_threshold or 0.0
        if self.confidence < threshold:
            return self._park_review(_(
                "Confidence %.2f below threshold %.2f.") % (self.confidence, threshold))

        partner, pmsg = self._resolve_partner(ex)
        if not partner:
            return self._park_review(pmsg)
        self.partner_id = partner

        duplicate = self._find_duplicate(ex, partner)
        if duplicate:
            return self.write({
                'state': 'duplicate', 'move_id': duplicate.id,
                'error_message': _("Duplicate of %s.") % duplicate.name})

        move = self._apply_to_move(ex, partner)
        self.write({'move_id': move.id, 'state': 'resolved', 'error_message': False})
        self.message_post(body=_("Draft vendor bill %s ready.") % move.name)

    def _park_review(self, reason):
        self.write({'state': 'needs_review', 'error_message': reason})
        self.message_post(body=_("Needs review: %s") % reason)

    def _partner_vals(self, supplier):
        """Map the extracted supplier block to res.partner values (truthy only)."""
        country = self.env['res.country'].search(
            [('code', '=', (supplier.get('country_code') or '').upper())], limit=1)
        vals = {
            'name': supplier.get('name'),
            'vat': supplier.get('vat'),
            'country_id': country.id or False,
            'street': supplier.get('street') or supplier.get('address_text'),
            'city': supplier.get('city'),
            'zip': supplier.get('zip'),
            'email': supplier.get('email'),
            'phone': supplier.get('phone'),
            'company_registry': supplier.get('registration_id'),
        }
        # DIČ (tax id) — extracted, or derived from a Slovak IČ DPH (SK + DIČ digits).
        # The field is localization-specific, so only set it where it exists.
        if 'tax_id' in self.env['res.partner']._fields:
            vat = (supplier.get('vat') or '').strip()
            dic = supplier.get('dic') or (vat[2:] if vat[:2].upper() == 'SK' else None)
            if dic:
                vals['tax_id'] = dic
        return {k: v for k, v in vals.items() if v}

    @staticmethod
    def _sanitize_iban(iban):
        return (iban or '').replace(' ', '').strip().upper()

    @classmethod
    def _bank_code(cls, iban):
        """Slovak bank code (positions 5-8 of a SK IBAN), or None."""
        s = cls._sanitize_iban(iban)
        return s[4:8] if len(s) >= 8 and s[:2] == 'SK' else None

    def _supplier_ibans(self, supplier):
        """Printed bank accounts, de-duplicated, original order (legacy `iban` too)."""
        raw = list(supplier.get('bank_accounts') or [])
        if supplier.get('iban'):
            raw.append(supplier['iban'])
        seen, out = set(), []
        for iban in raw:
            key = self._sanitize_iban(iban)
            if key and key not in seen:
                seen.add(key)
                out.append(iban.strip())
        return out

    def _ensure_banks(self, partner, supplier):
        """Create each printed supplier bank account not already present (deduped)."""
        if not self.company_id.ai_extract_auto_create_bank:
            return
        existing = {self._sanitize_iban(b.acc_number) for b in partner.bank_ids}
        for iban in self._supplier_ibans(supplier):
            if self._sanitize_iban(iban) not in existing:
                self.env['res.partner.bank'].create({'acc_number': iban, 'partner_id': partner.id})
                existing.add(self._sanitize_iban(iban))

    def _select_recipient_bank(self, ex, move):
        """Set the bill's recipient to the supplier account at the same bank as our
        highest-priority own account (an intra-bank transfer). Preference follows OUR own
        bank-account order, so with several own banks the primary one wins; falls back to
        the first printed supplier account."""
        printed = self._supplier_ibans(ex.get('supplier') or {})
        if not printed:
            return
        by_iban = {self._sanitize_iban(b.acc_number): b for b in move.partner_id.bank_ids}
        # supplier accounts that exist on the partner, kept in printed order
        supplier_banks = [by_iban[self._sanitize_iban(i)]
                          for i in printed if self._sanitize_iban(i) in by_iban]
        if not supplier_banks:
            return
        for own in move.company_id.partner_id.bank_ids:  # our accounts, in our order
            code = self._bank_code(own.acc_number)
            if not code:
                continue
            match = next((b for b in supplier_banks if self._bank_code(b.acc_number) == code), None)
            if match:
                move.partner_bank_id = match
                return
        move.partner_bank_id = supplier_banks[0]

    def _enrich_partner(self, partner, supplier):
        """Fill blank fields on a matched partner — never overwrite existing data."""
        vals = self._partner_vals(supplier)
        for identity in ('name', 'vat'):  # never touch the matched identity
            vals.pop(identity, None)
        to_fill = {k: v for k, v in vals.items() if not partner[k]}
        if to_fill:
            partner.write(to_fill)
        self._ensure_banks(partner, supplier)

    def _resolve_partner(self, ex):
        supplier = ex.get('supplier') or {}
        vat = normalize_vat(supplier.get('vat'))
        Partner = self.env['res.partner']
        if vat:
            match = Partner.with_context(active_test=False).search(
                [('vat', '!=', False)]
            ).filtered(lambda p: normalize_vat(p.vat) == vat)[:1]
            if match:
                self._enrich_partner(match, supplier)
                return match, ''
        if self.company_id.ai_extract_auto_create_partner:
            partner = Partner.create({
                **self._partner_vals(supplier),
                'name': supplier.get('name') or _("Unknown supplier"),
                'is_company': True,
                'supplier_rank': 1,
            })
            self._ensure_banks(partner, supplier)
            partner.message_post(body=_("Auto-created from AI invoice extraction %s.") % self.name)
            return partner, ''
        return False, _(
            "No supplier matched VAT '%s' (auto-create is disabled)."
        ) % (supplier.get('vat') or '—')

    def _find_duplicate(self, ex, partner):
        number = (ex.get('invoice') or {}).get('number')
        if not number:
            return self.env['account.move']
        domain = [
            ('move_type', 'in', ('in_invoice', 'in_refund')),
            ('company_id', '=', self.company_id.id),
            ('partner_id', '=', partner.id),
            ('ref', '=', number),
        ]
        if self.move_id:  # the alias-created bill we are about to fill is not a dup of itself
            domain.append(('id', '!=', self.move_id.id))
        return self.env['account.move'].search(domain, limit=1)

    def _resolve_fiscal_position(self, partner):
        return partner.property_account_position_id or \
            self.env['account.fiscal.position']._get_fiscal_position(partner)

    def _is_reverse_charge_fp(self, fiscal_position):
        """True if the fiscal position maps the standard domestic tax onto a tax
        that nets the VAT out (a reverse-charge tax has a negative repartition
        factor). Deterministic — based on the chart, not the model's hint."""
        if not fiscal_position:
            return False
        standard = self.company_id._ai_extract_tax_for_rate(
            self.company_id.ai_extract_reverse_charge_rate or 23.0)
        if not standard:
            return False
        return any(
            rl.factor_percent < 0
            for tax in fiscal_position.map_tax(standard)
            for rl in tax.invoice_repartition_line_ids
            if rl.repartition_type == 'tax'
        )

    def _vat_breakdown_lines(self, ex):
        """One synthetic line per VAT rate, from the (always-reconciling) breakdown."""
        inv = ex.get('invoice') or {}
        return [
            {'description': _("Invoice %s (%s%% VAT)") % (inv.get('number'), b.get('rate_percent')),
             'net': b.get('base'), 'vat_rate_percent': b.get('rate_percent')}
            for b in (ex.get('vat_breakdown') or [])
        ]

    # Section-summary row labels that duplicate the detail above them.
    _SUBTOTAL_KEYWORDS = ('spolu', 'súčet', 'sucet', 'medzisúčet', 'medzisucet',
                          'celkom', 'subtotal')

    def _is_subtotal_line(self, line):
        desc = (line.get('description') or '').lower()
        return any(kw in desc for kw in self._SUBTOTAL_KEYWORDS)

    def _source_lines(self, ex):
        """Choose the invoice-line source, preserving detail wherever possible.

        Returns (lines, rebuilt) where `rebuilt` flags that detail was discarded:
        - lines reconcile to the net total -> use them as-is;
        - lines OVER-count (section subtotals like "spolu" were double-counted) -> drop
          the summary rows and keep the real detail if that reconciles;
        - lines UNDER-count -> the normal advance/credit-deduction case, keep detail;
        - only when the duplicates can't be isolated -> rebuild from the VAT breakdown."""
        lines = ex.get('lines') or []
        net_total = (ex.get('totals') or {}).get('net')
        if not lines:
            return self._vat_breakdown_lines(ex), False
        if net_total is None:
            return lines, False
        net_total = float(net_total)
        tolerance = max(0.02, abs(net_total) * 0.005)
        line_sum = sum(float(line.get('net') or 0.0) for line in lines)
        # Reconciles, or under-counts (legitimate deductions) -> keep all detail.
        if line_sum - net_total <= tolerance:
            return lines, False
        # Over-counts -> drop summary rows and keep the detail if it then reconciles.
        detail = [line for line in lines if not self._is_subtotal_line(line)]
        detail_sum = sum(float(line.get('net') or 0.0) for line in detail)
        if detail and abs(detail_sum - net_total) <= tolerance:
            return detail, False
        # Couldn't isolate the duplicates -> fall back to the VAT breakdown.
        return self._vat_breakdown_lines(ex), True

    def _build_line_commands(self, source, fiscal_position):
        """Build invoice-line commands from the chosen source lines, with the domestic
        tax mapped through the fiscal position (so EU suppliers get the reverse-charge
        tax automatically).

        On a reverse-charge fiscal position the invoice itself shows 0% VAT, but the
        Slovak buyer must self-assess at the standard rate — so 0%-rated lines are taxed
        at the configured reverse-charge rate, which the fiscal position then remaps to
        the reverse-charge tax."""
        company = self.company_id
        expense = company.ai_extract_expense_account_id
        reverse_charge = self._is_reverse_charge_fp(fiscal_position)
        rc_rate = company.ai_extract_reverse_charge_rate or 23.0
        commands = []
        for line in source:
            rate = line.get('vat_rate_percent')
            if reverse_charge and not rate:
                rate = rc_rate
            tax = company._ai_extract_tax_for_rate(rate)
            if tax and fiscal_position:
                tax = fiscal_position.map_tax(tax)
            commands.append((0, 0, {
                'name': line.get('description') or '/',
                'quantity': 1.0,
                'price_unit': line.get('net') or 0.0,
                'account_id': expense.id if expense else False,
                'tax_ids': [(6, 0, tax.ids)] if tax else [(5, 0, 0)],
            }))
        return commands

    def _reconcile_tax_amounts(self, ex, move):
        """Pin each tax group's amount to the supplier's stated VAT.

        Suppliers (esp. B2C retailers) anchor on gross prices and back-derive VAT,
        so Odoo's per-line recompute can be off by a cent. We push the stated VAT
        through the native tax_totals inverse (the same path the bill's tax-totals
        widget uses for a manual override). Reverse-charge groups have a stated VAT
        of 0 and are left untouched."""
        by_rate = {
            round(float(b.get('rate_percent') or 0), 2): float(b.get('vat_amount') or 0)
            for b in (ex.get('vat_breakdown') or [])
        }
        if not by_rate:
            return
        targets = {}
        for tax_line in move.line_ids.filtered(lambda l: l.display_type == 'tax'):
            rate = round(tax_line.tax_line_id.amount, 2)
            if rate in by_rate:
                targets[tax_line.tax_group_id.id] = targets.get(tax_line.tax_group_id.id, 0.0) + by_rate[rate]
        if not targets:
            return
        totals = move.tax_totals
        changed = False
        for subtotal in totals.get('subtotals', []):
            for group in subtotal.get('tax_groups', []):
                target = targets.get(group['id'])
                if target is not None and not move.currency_id.is_zero(
                        group.get('tax_amount_currency', 0.0) - target):
                    group['tax_amount_currency'] = target
                    changed = True
        if changed:
            move.tax_totals = totals

    @staticmethod
    def _normalize_invoice_dates(inv):
        """Correct a common model mix-up where the taxable supply date and the due date
        are transposed: a supply date later than the due date almost always means the
        model read 'Dátum splatnosti' as the supply and vice-versa. Returns (inv, swapped)."""
        delivery, due = inv.get('delivery_date'), inv.get('due_date')
        if delivery and due and delivery > due:
            return {**inv, 'delivery_date': due, 'due_date': delivery}, True
        return inv, False

    def _apply_to_move(self, ex, partner):
        """Fill the linked draft bill (from the email alias / manual button), or
        create a new draft if none is linked."""
        company = self.company_id
        inv, dates_swapped = self._normalize_invoice_dates(ex.get('invoice') or {})
        classification = ex.get('classification') or {}
        currency = self.env['res.currency'].search(
            [('name', '=', (inv.get('currency') or 'EUR').upper())], limit=1
        ) or company.currency_id
        fp = self._resolve_fiscal_position(partner)
        source, lines_rebuilt = self._source_lines(ex)
        line_commands = self._build_line_commands(source, fp)

        common = {
            'partner_id': partner.id,
            'currency_id': currency.id,
            'invoice_date': inv.get('issue_date') or False,
            'invoice_date_due': inv.get('due_date') or False,
            'ref': inv.get('number') or False,
            'payment_reference': inv.get('variable_symbol') or inv.get('payment_ref') or False,
            'fiscal_position_id': fp.id if fp else False,
        }
        # Taxable supply date (Dátum uskutočnenia daňového plnenia) — l10n_sk only.
        # Tax point from the document, falling back to the bill date.
        move_fields = self.env['account.move']._fields
        if 'taxable_supply_date' in move_fields:
            common['taxable_supply_date'] = (
                inv.get('delivery_date') or inv.get('issue_date') or False)
        # Slovak payment symbols (VS/KS/SS) — localization-specific custom fields, guarded.
        symbols = {
            'variable_symbol': inv.get('variable_symbol') or inv.get('payment_ref'),
            'constant_symbol': inv.get('constant_symbol'),
            'specific_symbol': inv.get('specific_symbol'),
        }
        for fname, value in symbols.items():
            if fname in move_fields and value:
                common[fname] = value

        target = self.move_id if (self.move_id and self.move_id.state == 'draft') else False
        if target:
            target.write({**common, 'invoice_line_ids': [(5, 0, 0)] + line_commands})
            move = target
        else:
            journal = company.ai_extract_journal_id or self.env['account.journal'].search(
                [('type', '=', 'purchase'), ('company_id', '=', company.id)], limit=1)
            move_type = 'in_refund' if classification.get('document_type') == 'credit_note' else 'in_invoice'
            move = self.env['account.move'].create({
                **common,
                'move_type': move_type,
                'company_id': company.id,
                'journal_id': journal.id if journal else False,
                'invoice_line_ids': line_commands,
            })
            self.attachment_id.copy({'res_model': 'account.move', 'res_id': move.id})

        move.ai_extract_extraction_id = self.id
        self._select_recipient_bank(ex, move)
        self._reconcile_tax_amounts(ex, move)
        self._cross_check_reverse_charge(ex, move)
        self._flag_period_mismatch(move)
        if dates_swapped:
            move.message_post(body=_(
                "Swapped the taxable supply date and the due date — the extracted supply "
                "date was after the due date, which almost always means the two were "
                "transposed. Verify against the invoice."))
        if lines_rebuilt:
            move.message_post(body=_(
                "⚠ The extracted line items over-counted the invoice total (likely a "
                "subtotal row was double-counted) — the bill was rebuilt from the VAT "
                "summary so the total is correct. Review the line detail."))
        self._check_printed_total(ex, move)
        return move

    def _check_printed_total(self, ex, move):
        """Cross-check the bill total against the invoice's printed grand total (an
        independent anchor — the lines/breakdown can be self-consistent yet still wrong).

        A small drift is per-line rounding of sub-cent unit prices: absorb it with a
        transparent rounding line so the amount paid matches the invoice exactly. A gap
        too large to be rounding means the extraction is likely incomplete — flag it for
        review rather than silently paying the wrong amount."""
        due = (ex.get('totals') or {}).get('amount_due')
        if due is None:
            return
        diff = float(due) - move.amount_total
        if move.currency_id.is_zero(diff):
            return
        expense = move.company_id.ai_extract_expense_account_id
        # Max plausible per-line rounding is half a cent per line; allow that plus a buffer.
        rounding_band = 0.005 * len(move.invoice_line_ids) + 0.02
        if expense and move.currency_id.compare_amounts(abs(diff), rounding_band) <= 0:
            move.write({'invoice_line_ids': [(0, 0, {
                'name': _("Rounding difference (invoice total)"),
                'quantity': 1.0,
                'price_unit': diff,
                'account_id': expense.id,
                'tax_ids': [(5, 0, 0)],
            })]})
            self._reconcile_tax_amounts(ex, move)  # re-pin VAT after the added line
            move.message_post(body=_(
                "Per-line rounding left the bill %(d).2f off the invoice's printed total "
                "%(t).2f; added a rounding line so the total matches exactly."
            ) % {'d': diff, 't': float(due)})
        else:
            move.message_post(body=_(
                "⚠ Total check: the bill total %(c).2f does not match the invoice's printed "
                "amount due %(t).2f (off by %(d).2f) — the extraction may be incomplete; "
                "review before posting."
            ) % {'c': move.amount_total, 't': float(due), 'd': diff})

    def _flag_period_mismatch(self, move):
        """Optional guard: warn when the tax point falls outside the expected window
        relative to the bill date — i.e. *after* the bill date (a tax point that
        post-dates the invoice, usually a mis-read), or earlier than the month before
        it (a stale tax point). A supply date in the bill's month or the prior month
        is the normal case (an invoice for last period issued early this period) and is
        not flagged."""
        if not self.company_id.ai_extract_flag_period_mismatch:
            return
        supply = move._fields.get('taxable_supply_date') and move.taxable_supply_date
        bill = move.invoice_date
        if not (supply and bill):
            return
        if supply > bill:
            move.message_post(body=_(
                "⚠ Tax-point check: taxable supply date %(s)s is after the bill date "
                "%(b)s — unusual for a received invoice; verify the tax point before posting."
            ) % {'s': supply, 'b': bill})
        elif supply < bill.replace(day=1) - relativedelta(months=1):
            move.message_post(body=_(
                "⚠ Tax-point check: taxable supply date %(s)s is older than the month "
                "before the bill date %(b)s — verify the tax point before posting."
            ) % {'s': supply, 'b': bill})

    def _cross_check_reverse_charge(self, ex, move):
        classification = ex.get('classification') or {}
        model_rc = bool(classification.get('reverse_charge')
                        or classification.get('intra_eu_acquisition'))
        # Applied RC == any tax line whose repartition nets the VAT out (negative factor).
        applied_rc = any(
            rl.factor_percent < 0
            for tax in move.invoice_line_ids.tax_ids
            for rl in tax.invoice_repartition_line_ids
            if rl.repartition_type == 'tax'
        )
        if model_rc != applied_rc:
            move.message_post(body=_(
                "⚠ Reverse-charge mismatch — model suggested %(m)s, applied tax implies "
                "%(a)s. Please review the fiscal position / taxes."
            ) % {'m': model_rc, 'a': applied_rc})

    # ------------------------------------------------------------------
    # Cron
    # ------------------------------------------------------------------
    @api.model
    def _cron_sweep(self, limit=20):
        for rec in self.search([('state', 'in', ('pending', 'error'))], limit=limit):
            rec._process_one()
            self.env.cr.commit()  # isolate failures between documents
