Sends the money to the bailiff.

Payroll can only credit one collective liability account for the whole
garnishment total — a salary rule cannot be split per creditor, and on the
Enterprise engine the payslip line's partner comes from the salary rule, so it
cannot vary per employee either. This module closes that gap.

Per order and period it books::

    Dr  garnishment liability (collective, e.g. 379xxx)
        Cr  accounts payable of the bailiff / creditor, partner set

and stamps the entry with the case number as the variable symbol. What is left
is an ordinary open payable in the bailiff's name, which the existing
``account_payment_order`` and bank-file modules pay exactly like any supplier.

One entry per *order* rather than per payee: a bailiff commonly runs several
cases against the same employer and each needs its own variable symbol for the
receiving end to match it.

Configure the remittance journal and the garnishment liability account under
Accounting → Configuration → Settings.
