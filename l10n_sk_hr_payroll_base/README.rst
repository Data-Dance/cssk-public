============================================
Slovakia — Payroll Base (employment forms)
============================================

.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
   :alt: License: AGPL-3

**Engine-neutral base for the Slovak payroll: the employment forms (pracovný pomer, DoVP, DoPČ, DoBPŠ) and one table saying which contributions and entitlements apply to which of them.**

Engine-neutral foundation for the Slovak payroll.

Holds the four employment forms — pracovný pomer and the three dohody — and one
table (``applicability.py``) recording which social-insurance contributions and
which entitlements apply to each of them.

That table used to be thirty predicates spread across two engine-specific rule
files. It behaved like it: whether § 120 applies to dohody was answered
correctly in one place and incorrectly in another, one commit apart, because
nowhere could the answer be read as a whole.

Salary rules on both engines ask it directly::

    result = contract.l10n_sk_applies('SICKNESS_INSURANCE')

.. rubric:: Known issues / Roadmap

* ``NEEDS_LEGAL_CONFIRMATION`` lists rows deliberately not asserted: whether
  the 2023 amendment extended the §§ 122a-122c wage surcharges and the § 152
  meal entitlement to dohodári. Both are believed to apply and both are
  currently applied by the rules — but without a table row claiming so, since
  that is belief rather than checked law. Confirm with a practitioner and then
  encode.
* The table answers per employment form and income regularity. Finer
  eligibility — OOP, health exemption, ZŤP — stays on the contract, because it
  varies between two people on the same kind of agreement.
* Slovak only. The Czech localisation has one employment form in practice and
  no equivalent split, so no table is needed there yet.

.. rubric:: Module facts

- **Technical name:** ``l10n_sk_hr_payroll_base``
- **Version:** 18.0.1.0.0
- **Licence:** AGPL-3
- **Requires:** ``hr_contract``

Authors: Data Dance s.r.o.
