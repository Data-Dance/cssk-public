---
title: CZ/SK Wage Garnishments — Remittance
summary: Turns each order's garnishment deductions into a posted payable to the bailiff or creditor, with the case number as variable symbol, ready for the payment order and bank file.
verified: 19.0.1.1.2
family: l10n_cssk_hr_payroll_garnishment_base#accounting
---

Moves the garnishment deductions from the collective liability the payroll entry credits onto the payee: one posted entry per order, debiting the *Garnishment Liability Account* and crediting the bailiff's or creditor's payable, with the order's variable, specific and constant symbols and its payee bank account. The open payable is then paid like any supplier. Remit from *Employees → Garnishments → Remit to Payees*, or with *Remit to Payee* on selected deductions; remitted deductions can no longer be deleted, and their payslip cannot be set back to draft.

It installs itself when `account`, the garnishment register and the payment symbols module are installed. Set the *Garnishment Remittance Journal* and the *Garnishment Liability Account* under *Accounting → Configuration → Settings*, block *Wage Garnishments*. Remitting is available to the Accounting *Administrator* and to users with *Show Full Accounting Features*.
