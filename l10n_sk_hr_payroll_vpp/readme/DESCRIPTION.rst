Slovak **VPP** (Výkaz poistného a príspevkov) — the social-insurance statement
filed to the Sociálna poisťovňa for employees with **irregular income**
(nepravidelný príjem), i.e. work agreements (dohody: DoVP / DoPČ), and for
regular income paid after the insurance relationship has ended. It is the
dohoda counterpart of the monthly MVP.

Like the MVP it produces both the employer-aggregate summary (``poistne``) and
the full per-employee annex (``priloha/poistneZamestnancov/poistneZamestnanca``),
reusing the same Slovak social rule-code → fund mapping (np↔SICK, sp↔PENSION,
ip↔DISABILITY, pvn↔UNEMPLOYMENT, up↔ACCIDENT, gp↔GUARANTEE, rfs↔RESERVEFUND).
The exported XML (ns ``http://socpoist.sk/xsd/vpp2026``) is validated against
the shipped ``VPP-v2026.xsd``.

It is **scoped to dohoda contracts**: only payslips whose employee has an
``l10n_sk_agreement_type`` of ``dovp`` (DoVP) or ``dopc`` (DoPČ) are collected.
The header carries ``cisloVykazu`` (MM99RRRR) and ``obdobieVyplPrijmov``
(MMRRRR); the annex ``typZec`` defaults to the *irregular-income* relationship
code (DoVP → ``ZECD1N``, DoPČ → ``ZECD2N``).

Engine-neutral: it reads payslips through the shared
``l10n_cssk_payroll_declaration_base`` adapter and works on both the
``payroll`` engine and the ``hr_payroll`` engine.
