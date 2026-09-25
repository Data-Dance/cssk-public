In both the Czech Republic and Slovakia a court, a bailiff or an
administrative authority can order that part of an employee's wage be
withheld and paid straight to the creditor. The employer is not a bystander
in that process: it must rank the orders, apply a statutory waterfall across
all of them, remit the money and answer to the court for what it did.

This module is the engine-neutral foundation for that. It ships:

* **The register** — ``hr.wage.garnishment``, one record per order served on
  the employer: case number, claim class, the *day it was delivered* (which
  is what legally establishes the rank), the creditor, the bailiff, the bank
  account and payment symbols it must be remitted to, the total claim and the
  running balance.
* **The deduction ledger** — ``hr.wage.garnishment.line``, one row per order
  per payslip, recording not just the amount but *which third* it came from,
  so the calculation is auditable years later.
* **The allocator** — a pure-Python, Odoo-free implementation of the statutory
  waterfall, unit tested in isolation:

  * Czech Republic: ``§ 276-§ 302 o. s. ř.`` + ``nařízení vlády 595/2006 Sb.``
    — the nezabavitelná částka, the thirds, maintenance taking absolute
    precedence in the second third (pro rata by *current* maintenance,
    disregarding arrears), everything else strictly by pořadí, and the fully
    seizable part above the limit joining the second third only as far as the
    priority claims need it.
  * Slovakia: ``nariadenie vlády 268/2006 Z. z.`` — including the part most
    implementations get wrong, that the protected *základná suma* depends on
    what is being collected: 140 % ŽM for an ordinary claim, 100 % for a
    priority one, 70 % of 60 % for maintenance of a minor child, 50 % for an
    administrative fine, with the per-dependant addition doubling to 50 % for
    a pension recipient.

* **Dated statutory rates** — ``hr.wage.garnishment.rate``, so a new
  subsistence minimum is a data change, not a code change.
* **The employer's statutory paperwork** — a wizard producing the notices of
  a debtor joining or leaving, the answer to an enquiry about rank and
  amounts (``§ 294``, ``§ 295 o. s. ř.``), and the account of deductions
  (*vyúčtování srážek*).

The base depends on ``hr`` and ``mail`` only — never on a payroll engine. The
bridge modules wire it into the ``payroll`` (OCA) and ``hr_payroll``
(Enterprise) engines, and the accounting bridge turns each deduction into a
payable to the bailiff.
