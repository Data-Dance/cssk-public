import logging

_logger = logging.getLogger(__name__)

# VAT rates pre-mapped on install (SK: 23 current standard, 20 legacy, 19/10 reduced).
DEFAULT_RATES = (23, 20, 19, 10)


def _find_purchase_tax(env, company, rate):
    """Domestic purchase tax for a VAT rate, skipping reverse-charge taxes
    (which net the VAT out through a negative repartition factor)."""
    taxes = env['account.tax'].search([
        ('company_id', '=', company.id),
        ('type_tax_use', '=', 'purchase'),
        ('amount_type', '=', 'percent'),
        ('amount', '=', float(rate)),
    ])
    domestic = taxes.filtered(lambda t: not any(
        rl.factor_percent < 0
        for rl in t.invoice_repartition_line_ids
        if rl.repartition_type == 'tax'))
    return (domestic or taxes)[:1]


def _setup_tax_map(env, company):
    TaxMap = env['account.invoice.ai.tax.map']
    for rate in DEFAULT_RATES:
        if TaxMap.search([('company_id', '=', company.id), ('rate_percent', '=', rate)], limit=1):
            continue
        tax = _find_purchase_tax(env, company, rate)
        if tax:
            TaxMap.create({'company_id': company.id, 'rate_percent': rate, 'tax_id': tax.id})


def post_init_hook(env):
    """Pre-fill each company's AI-invoice config on install so the extractor
    works out of the box: a VAT-rate map plus a default provider and model.
    Existing settings are never overwritten."""
    provider = env['muk_ai.provider']._get_default()
    haiku = env['muk_ai.model'].search([('technical_name', '=', 'claude-haiku-4-5')], limit=1)
    for company in env['res.company'].search([]):
        _setup_tax_map(env, company)
        vals = {}
        if not company.ai_extract_provider_id and provider:
            vals['ai_extract_provider_id'] = provider.id
        if not company.ai_extract_model_id:
            model = haiku or (provider.default_model_id if provider else env['muk_ai.model'])
            if model:
                vals['ai_extract_model_id'] = model.id
        if vals:
            company.write(vals)
        _logger.info("account_invoice_ai_extract: initialized config for company %s", company.name)
