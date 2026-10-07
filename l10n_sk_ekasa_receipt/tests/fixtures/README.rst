=========================
About these fixtures
=========================

Two responses from Finančná správa's document-verification service, used to pin
the mapping in ``test_ekasa_mapping.py`` and the provider in
``test_ekasa_provider.py``.

**They are anonymised.** Everything that identifies a business or a purchase was
replaced with synthetic values: company names, IČO / DIČ / IČ DPH, addresses,
cash-register codes, receipt identifiers, OKP, item names and the dates. The
``pkp`` signature is elided.

**Everything that makes them useful is verbatim**, because the point of a fixture
fetched from a real service is that it reproduces what the real service does:

* every amount, quantity and VAT rate, so both receipts still reconcile to the
  cent — 181.90 across three rates, and 57.85 at 23 %;
* the response's field structure, including the fields that look like mistakes
  and are not.

The replacement identifiers were chosen to keep the structure meaningful: the
VAT numbers pass the Slovak check (divisible by eleven), and a cash-register
code is still ``888`` + the tax number + four digits.

What each fixture is here to prove
==================================

``receipt_offline_restaurant.json`` — an off-line receipt (the QR carries a
composite key, not an identifier), with:

* **three VAT rates at once** — 5 % food, 19 % a non-alcoholic drink, 23 %
  alcohol — which is routine in Slovak hospitality;
* a **legacy ``vatRateBasic`` / ``vatRateReduced`` pair still reading 20 / 10**,
  labels from the regime before 2025, sitting beside a correct ``vatSummary``.
  *Do not "fix" it.* It is the trap the mapper exists to avoid;
* a **zero-priced item** at 19 %, hence a VAT bucket with a zero base;
* an item name carrying **embedded newlines** whose modifiers are already inside
  the parent line's price;
* an ``okp`` in **upper case**;
* a real ``receiptId`` returned even though the printed receipt had none,
  because the till synced afterwards.

``receipt_online_fuel.json`` — an on-line receipt (the QR *is* the identifier),
with:

* the **entire legacy pair null** while ``vatSummary`` is populated — the other
  half of the reason that pair is never read;
* ``icDph`` that is **not** ``"SK" + dic``, as for a member of a VAT group;
* a **fractional quantity** (31.17) whose unit price is not representable at two
  decimals, which is why line quantities are never posted as quantities;
* ``issueDate`` one second **after** ``createDate``;
* an ``okp`` in **lower case**.
