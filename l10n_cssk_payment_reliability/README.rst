======================================================
CZ/SK Supplier Reliability Check (guarantor liability)
======================================================

Protects the **buyer** from liability for a supplier's unpaid VAT
(*ručenie za daň* §69 ods. 14 SK / *ručení* §109 CZ). Before you pay a vendor
bill, it checks the supplier's **tax reliability** rating and whether the bank
account you are about to pay is one the supplier has **registered / published**
with the tax authority, then **snapshots the result onto the bill** as
point-in-time proof.

This is the **country-neutral base**. The actual register lookups live in the
country providers (e.g. ``l10n_sk_payment_reliability``); without a provider the
base reports "nothing available" and never blocks anything. Works on Community
and Enterprise.

Features
========

* Vendor-bill reliability check: the supplier's tax-reliability rating
  (highly reliable / reliable / less reliable / unreliable / unknown).
* Registered bank-account check: is the account being paid among the accounts
  the supplier published with the tax authority?
* Point-in-time **snapshot on the bill** — status, the registered accounts and a
  timestamp — kept as proof, plus a warning posted to the chatter.
* **Never blocks** the payment: paying an unregistered account or an unreliable
  payer stays possible (you may instead remit the VAT directly to the tax office
  under §69b SK / §109a CZ); you are only warned and it is documented.
* **VAT-deregistration listing** where the country provides it (SK: the list of
  VAT payers with grounds for cancelling their registration).
* Optional **auto-check** (per company) when a vendor bill is posted, **again
  when an outbound supplier payment is posted** — against the account actually
  paid, since that is what the liability attaches to — and **daily for bills
  still unpaid**. Fails safe: a register hiccup never blocks posting.

Usage
=====

Enable the auto-check in *Settings ▸ Accounting* if wanted. On any vendor bill,
press **Check supplier reliability** next to the recipient bank account; the
snapshot fields fill in and, if the account is unregistered or the payer is
rated less reliable / unreliable, a warning banner appears at the top of the
bill and a note is posted to the chatter. The partner form also carries the last
tax-reliability rating and check date.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
