Czech payroll rules for the ``payroll`` engine. This module implements the
monthly payslip for standard employment (pracovní poměr) according to Czech
legislation, including social and health insurance, the income-tax advance and
the child tax benefit/bonus.

The statutory figures are taken from Czech primary sources (ČSSZ, Finanční
správa, MPSV, health insurers) and documented, with the effective dates and
source URLs, in ``docs/cz_payroll_legal.md``.

All statutory rates and thresholds are stored as dated rule parameters
(``hr.rule.parameter`` / ``hr.rule.parameter.value``) for 2025 and 2026;
``payslip.rule_parameter(code)`` resolves the value effective at the payslip
date.
