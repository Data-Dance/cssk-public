# The forced-tool schema Claude must call. Natural keys only — never Odoo IDs.
EXTRACT_INVOICE_TOOL = {
    'name': 'extract_invoice',
    'description': (
        "Return the structured data extracted from the attached supplier invoice "
        "PDF. Provide natural keys only (VAT numbers, ISO currency/country codes, "
        "dates, amounts) — never database IDs, tax IDs or fiscal positions."
    ),
    'parameters': {
        'type': 'object',
        'additionalProperties': False,
        'required': ['supplier', 'invoice', 'totals', 'vat_breakdown', 'lines', 'classification'],
        'properties': {
            'supplier': {
                'type': 'object',
                'required': ['name'],
                'properties': {
                    'name': {'type': 'string'},
                    'vat': {'type': ['string', 'null'],
                            'description': "VAT / IČ DPH incl. country prefix, e.g. SK2020123456, CZ12345678"},
                    'country_code': {'type': ['string', 'null'], 'description': "ISO 3166-1 alpha-2"},
                    'registration_id': {'type': ['string', 'null'], 'description': "IČO / company registration number (HRB, etc.)"},
                    'dic': {'type': ['string', 'null'], 'description': "DIČ — tax identification number (Slovak DIČ, ~10 digits); distinct from the IČ DPH / VAT number"},
                    'bank_accounts': {'type': 'array', 'items': {'type': 'string'},
                                      'description': "All bank accounts (IBANs) printed for payment, in order; list every one when several banks are shown (\"pay to any of the listed accounts\")"},
                    'street': {'type': ['string', 'null'], 'description': "Street and house number"},
                    'city': {'type': ['string', 'null']},
                    'zip': {'type': ['string', 'null'], 'description': "Postal code"},
                    'address_text': {'type': ['string', 'null'], 'description': "Full address as printed (fallback if street/city/zip can't be split)"},
                    'email': {'type': ['string', 'null']},
                    'phone': {'type': ['string', 'null']},
                },
            },
            'invoice': {
                'type': 'object',
                'required': ['number', 'issue_date', 'currency'],
                'properties': {
                    'number': {'type': 'string', 'description': "Supplier's invoice number"},
                    'issue_date': {'type': 'string', 'description': "YYYY-MM-DD"},
                    'due_date': {'type': ['string', 'null'], 'description': "YYYY-MM-DD"},
                    'delivery_date': {'type': ['string', 'null'], 'description': "Tax point / dátum dodania, YYYY-MM-DD"},
                    'currency': {'type': 'string', 'description': "ISO 4217, e.g. EUR"},
                    'order_ref': {'type': ['string', 'null'], 'description': "Purchase order reference if present"},
                    'payment_ref': {'type': ['string', 'null'], 'description': "Payment reference (defaults to the variable symbol)"},
                    'variable_symbol': {'type': ['string', 'null'], 'description': "Variabilný symbol (VS)"},
                    'constant_symbol': {'type': ['string', 'null'], 'description': "Konštantný symbol (KS)"},
                    'specific_symbol': {'type': ['string', 'null'], 'description': "Špecifický symbol (SS)"},
                },
            },
            'totals': {
                'type': 'object',
                'required': ['net', 'vat', 'gross'],
                'properties': {
                    'net': {'type': 'number'},
                    'vat': {'type': 'number'},
                    'gross': {'type': 'number'},
                    'amount_due': {'type': ['number', 'null'],
                                   'description': "Grand total to pay as printed prominently (Spolu/Suma na úhradu); "
                                                  "equals gross unless an advance/credit is deducted — then it is the net amount due"},
                },
            },
            'vat_breakdown': {
                'type': 'array',
                'description': "One entry per distinct VAT rate; must reconcile to totals.",
                'items': {
                    'type': 'object',
                    'required': ['rate_percent', 'base', 'vat_amount'],
                    'properties': {
                        'rate_percent': {'type': 'number'},
                        'base': {'type': 'number'},
                        'vat_amount': {'type': 'number'},
                    },
                },
            },
            'lines': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'required': ['description', 'net', 'vat_rate_percent'],
                    'properties': {
                        'description': {'type': 'string'},
                        'qty': {'type': ['number', 'null']},
                        'unit_price': {'type': ['number', 'null']},
                        'net': {'type': 'number'},
                        'vat_rate_percent': {'type': 'number'},
                    },
                },
            },
            'classification': {
                'type': 'object',
                'required': ['document_type', 'confidence'],
                'properties': {
                    'document_type': {'type': 'string', 'enum': ['invoice', 'credit_note', 'proforma']},
                    'reverse_charge': {'type': 'boolean',
                                       'description': "Invoice indicates reverse charge / prenesenie daňovej povinnosti (§69)"},
                    'intra_eu_acquisition': {'type': 'boolean',
                                             'description': "Intra-EU acquisition of goods (nadobudnutie tovaru z EÚ)"},
                    'confidence': {'type': 'number', 'description': "0..1 overall confidence"},
                },
            },
        },
    },
}
