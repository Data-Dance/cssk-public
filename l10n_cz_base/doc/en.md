---
title: Czech Base Localization (bank account numbers)
summary: Shows a Czech IBAN in the domestic form — prefix, account number and bank code — and converts between the two for the modules that need it.
verified: 19.0.2.0.4
---

## What it is for {#purpose}

A Czech bank account has two written forms: the **IBAN**
(`CZ65 0800 0000 1920 0014 5399`) and the **domestic form**
(*číslo účtu v národním formátu*), `19-2000145399/0800` — an optional prefix
(*předčíslí*), the account number and the four-digit bank code
(*kód banky*). Czech counterparties, bank files and documents such as ISDOC
still use the domestic form.

Odoo stores one account number. This module keeps the IBAN as that number and
derives the domestic parts from it, so both are available. It is a building
block: [module:account_edi_isdoc](module:account_edi_isdoc) relies on it to
write and read the domestic form, and other modules use its conversion.

It also keeps the old field names of the payment symbols for one release (see
[Payment symbols](#symbols)).

## Legal background {#legal}

The structure of a Czech account number is set by
[ČNB decree No. 169/2011 Sb.](law:cz/2011/169): the IBAN has 24 characters —
`CZ`, two check digits, the four-digit bank code (§ 6) and the 16-digit
account identifier (§ 5), which consists of a prefix of up to 6 digits and an
account number of 2 to 10 digits, leading zeros being insignificant (§ 4, § 5).

## Bank accounts {#bank-accounts}

On a bank account (*Contacts → a contact → Invoicing tab → Bank Accounts*,
or *Accounting → Configuration → Bank Accounts*), three read-only fields
appear after *Account Number*:

| Field (Czech label) | Example | Content |
|---|---|---|
| Bank Code (*Kód banky*) | `0800` | characters 5–8 of the IBAN |
| Legacy Account Starting Number (*Předčíslí účtu ve starém formátu*) | `000019` | characters 9–14 |
| Legacy Account Number (*Číslo účtu ve starém formátu*) | `2000145399` | characters 15–24 |

Enter the **IBAN** as the account number and the three fields fill in when you
save. They are computed and cannot be edited. For an account that is not a
Czech IBAN they stay empty.

## Conversion for other modules {#conversion}

Modules that exchange documents with Czech systems use the module's
conversion in both directions:

- the domestic form for a stored account: `19-2000145399` and bank code
  `0800`, with leading zeros removed;
- an IBAN from a domestic number found in an incoming document
  (`19-2000145399/0800`), with the check digits calculated, so the account can
  be matched or created in IBAN form.

An account that was entered in the domestic form rather than as an IBAN is
still understood by this conversion: the IBAN is calculated from it.

## Payment symbols {#symbols}

The variable, constant and specific symbols are provided by
[module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols), which
this module installs. Older versions of this module had their own symbol
fields; they were merged into the shared ones on upgrade, and the old
technical names (`variable_symbol`, `constant_symbol`, `specific_symbol`)
remain as aliases of the shared fields for one more release so that older
integrations keep working. There is nothing to see or set here; use the
payment symbols guide.

## Limitations {#limitations}

- The domestic parts are derived only from an IBAN. If an account number is
  entered in the domestic form, the three fields stay empty (other modules
  can still convert it, see above).
- The account number is not checked against the ČNB weighted checksum
  (annex to decree 169/2011 Sb.) or against the list of bank codes; an IBAN is
  validated only as far as Odoo validates IBANs.
- The prefix is shown with leading zeros (`000019`) in the field, without them
  in converted output.
- The legacy symbol field names are scheduled to be removed; integrations
  should move to the `l10n_cssk_*` fields.
