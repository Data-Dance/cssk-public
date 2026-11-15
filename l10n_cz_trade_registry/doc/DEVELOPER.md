# l10n_cz_trade_registry: developer notes

Not user documentation: this file is not rendered into a page.

## Wording decisions

- Idiomatic Czech says *zapsaná / zapsaný / zapsané v obchodním rejstříku …*,
  and the participle follows the grammatical gender of the legal form
  (společnost, spolek, družstvo). The module does not know the legal form, so
  the statement is built around the register: *Obchodní rejstřík vedený
  Městským soudem v Praze, oddíl C, vložka 12345*. The only agreement left is
  *vedený* with *rejstřík*, the head noun of all six veřejné rejstříky.
- The court goes into the **instrumental** (*Městským soudem*, *Krajským
  soudem*) from a table of two prefixes. The official court names carry the
  seat in the locative already (*v Praze*, *v Brně*), so nothing else declines.
- The register is recognised against the six names of § 1 odst. 1 zákona
  č. 304/2013 Sb. Only for those is the *vedený … soudem* and *oddíl / vložka*
  wording used: it is their vocabulary. Another evidence numbers its entries
  its own way, and the živnostenský rejstřík is not "kept" by the obecní
  živnostenský úřad a subject deals with, so an authority entered next to it
  is joined by a comma, not by *vedený*.
- Anything the tables do not recognise passes through **verbatim**. A stiff
  statement is a much better failure than a confidently wrong one.
- A spisová značka names the rejstříkový soud itself, never one of its
  pobočky: ARES's `SoudVr` codelist holds the Městský soud v Praze and six
  krajské soudy (České Budějovice, Plzeň, Ústí nad Labem, Hradec Králové,
  Brno, Ostrava) and no pobočka.

## Status

Codes follow ARES's `StavZdroje` codelist: `AKTIVNI`, `POZASTAVENY`,
`ZANIKLY`, `HISTORICKY`. `NEEXISTUJICI` ("this source holds no such subject"),
`BUDOUCI` and `LOGICKY_SMAZANY` parse to nothing: they describe ARES's record,
not the subject.

## Where the data comes from

`partner_autocomplete_ares_cz` fills the coordinates, the status, the dates,
the check timestamp and the two lists on every enrichment — by its
configurable mapping and by feature detection, so neither module depends on
the other. That module applies its default mappings when it is installed or
upgraded; `post_init_hook` here asks it to do so again, for the case where it
was installed first.

## What the Slovak twin has and this module does not

- **Filed financial statements** (`l10n.sk.register.filing`): the Czech ones
  are in the sbírka listin, which ARES does not republish.
- **Legal form and size category**: ARES gives codes, not the register's
  words, and a field holding a bare code helps nobody.
- **Suspension of a single activity**: a veřejný rejstřík entry has entered
  and deleted, no suspended.
- **"Ask the register to re-read"**: ARES has no such call.
- **Greyed-out row in the contact list**: `decoration-muted` on the list holds
  one expression and the Slovak twin, which can be installed in the same
  database, sets it.
- **Dependency on `partner_nace`**: nothing here uses the NACE code.
