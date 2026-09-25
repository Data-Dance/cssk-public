Monthly Czech **PVPOJ** (Přehled o výši pojistného) — the employer social-
insurance overview filed to the ČSSZ by the 20th of the following month.

The overview is **employer-aggregate**: it sums the employer and employee
social premiums for the period from the payslip rule codes ``SOCIALERTOT`` and
``SOCIALEETOT`` and exports the official XML (ns
``http://schemas.cssz.cz/POJ/PVPOJ2025``), validated against the shipped
``PVPOJ25.xsd`` (+ ``baseTypes2.xsd``).

Engine-neutral: it reads payslips through the shared
``l10n_cssk_payroll_declaration_base`` adapter and works on both the
``payroll`` engine and the ``hr_payroll`` engine.

**Part-time premium-discount annex (§7a sleva na pojistném):** when a payslip in
the period carries a ``SOCIAL_DISCOUNT`` line (the 5 % employer discount for
eligible part-time employees, driven by the ``l10n_cz_social_discount_category``
field on the employee), the report emits the aggregate ``slevaZamestnavatele``
block and the per-employee ``slevaZamestnanci`` annex (name, date of birth,
assessment base, ``duvodSlevy`` reason letter and shorter weekly working time),
and reduces ``pojistneUhrada`` by the discount. When nobody qualifies the
optional blocks are omitted and the output is unchanged.
