# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Czechia — Payroll Engine Parity Harness",
    "version": "19.0.1.2.1",
    "category": "Human Resources/Payroll",
    "summary": "Cross-engine parity harness: drives one shared set of payroll "
    "scenarios through both the OCA payroll and the Enterprise hr_payroll "
    "Czech implementations and asserts they produce identical figures.",
    "author": "Data Dance s.r.o.",
    "website": "https://github.com/Data-Dance/l10n_cssk",
    "license": "AGPL-3",
    "countries": ["cz"],
    # Deliberately depends on NEITHER engine: it is installed alongside
    # whichever one is under test, and detects it at runtime.
    "depends": [
        "hr",
        # For the shared rule-code map. Engine-neutral itself, so depending on
        # it does not compromise this module's own neutrality.
        "l10n_cssk_payroll_declaration_base",
    ],
    "installable": True,
}
