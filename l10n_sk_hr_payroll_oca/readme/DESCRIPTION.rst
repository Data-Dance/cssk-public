Slovak payroll rules for the ``payroll`` engine. This module implements the
monthly payslip for standard employment (pracovný pomer) according to Slovak
legislation, including social and health insurance, income tax and the child
tax bonus.

The statutory figures are taken from Slovak primary sources (Sociálna
poisťovňa, Finančná správa, MPSVR SR, health insurers) and documented, with the
effective dates and source URLs, in ``docs/sk_payroll_legal.md``.

All statutory rates and ceilings are stored as dated rule parameters
(``hr.rule.parameter`` / ``hr.rule.parameter.value``), so the year-to-year
differences are data, not code. ``payslip.rule_parameter(code)`` resolves the
value effective at the payslip date.
