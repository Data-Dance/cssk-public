# l10n_cz_vat_registration: developer notes

Not user documentation: this file is not rendered into a page.

## Why it does not block

It computes onto the form, and posts its reason to the chatter on posting. It
does not stop the posting, for the same reason
`l10n_cssk_payment_reliability` does not: the category is a copy of a
register, registrations change, and refusing to post an invoice on that basis
would be worse than the error it prevents.

## How a § 92a supply is recognised

Two signals on the tax, either of which is enough:

- a per-tax flag, detected at run time rather than depended on:
  `l10n_cz_invoice_reverse_charge` (`l10n_cz_invoice`) or
  `l10n_cz_reverse_charge` (another Czech localization, which
  `l10n_cz_invoice` honours too);
- the `VAT 25` tag on a base repartition line — row 25 of the return, "Režim
  přenesení daňové povinnosti (§ 92a) – dodavatel zboží nebo poskytovatel
  služeb" — which `l10n_cz`'s own *0% RC* sale tax carries. `l10n_cz` is a
  dependency, so this signal is always available; the tag is looked up with
  `account.account.tag._get_tax_tags`, which is how the report finds it.

A tax with neither is not known to be a reverse charge, and the check says
nothing about it.

## Vocabulary

`payer` / `identified` / `non_payer` are the keys `l10n_cz_vat_status` uses
for the company's own status over time. `group` is added because the register
names a skupina separately. That module answers "what was *our* status on the
date of this document"; this one records what a *counterparty* is today.

## The register's answer

`typSubjektu` of the Finanční správa web service
(`getStatusNespolehlivySubjektRozsirenyV2`): `PLATCE_DPH`,
`IDENTIFIKOVANA_OSOBA`, `SKUPINA_DPH`, `NENALEZEN`, `NESPOLEHLIVA_OSOBA`. The
last two parse to nothing. `NENALEZEN` is as often a mistyped DIČ as a
neplátce. A nespolehlivá osoba is not a plátce by definition, but the register
does not say whether it is an identifikovaná osoba, and the field has no value
for "one of the two". The service does not publish the date of registration,
so `l10n_cz_vat_payer_since` is entered by hand.

`l10n_cz_payment_reliability` makes the call and writes the field, by feature
detection; neither module depends on the other.
