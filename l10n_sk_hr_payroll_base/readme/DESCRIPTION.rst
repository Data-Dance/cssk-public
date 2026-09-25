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
