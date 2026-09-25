The Czech localisation exists in two engine flavours — ``l10n_cz_hr_payroll_oca``
on the OCA ``payroll`` engine and ``l10n_cz_hr_payroll_ee`` on Enterprise
``hr_payroll`` — and they are meant to be interchangeable. Until this module,
that was a convention rather than a checked property: each suite asserted its
own numbers in its own database, so a divergence introduced on one side would
surface as a wrong payslip rather than as a failing test.

This module holds ONE set of expected figures. Both engines are driven through
the same scenarios and asserted against it, so a divergence fails somewhere
instead of shipping.

It is the Czech counterpart of ``l10n_sk_hr_payroll_parity``, which has caught
three real divergences — an average-earnings divisor, a draft-payslip filter,
and a basic-wage proration base. Every one was found by accident first, because
no scenario happened to reach it. The scenarios here therefore aim at the seams
deliberately: real leaves rather than only payslip inputs, and a full-time week
that is not the same length every day.
