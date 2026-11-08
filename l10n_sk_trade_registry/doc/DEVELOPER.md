# l10n_sk_trade_registry: developer notes

Not user documentation: this file is not rendered into a page.

## Parsing decisions

- The register goes into the **locative** (*v Obchodnom registri*), the
  authority into the **genitive** (*Mestského súdu Bratislava III*), from a
  short table of fixed prefixes. The place name keeps the nominative form the
  register itself uses.
* **Zapísaná** for a company, **Zapísaný** for a sole trader.
* `oddiel` / `vložka` wording is used **only** for the Obchodný register —
  that is its own vocabulary. A Živnostenský register number can contain a
  slash too, and labelling its parts that way would put words on a statutory
  document that the issuing register does not use.
* Anything the tables do not recognise passes through **verbatim**. A slightly
  stiff sentence is a much better failure than a confidently wrong one.

An unrecognised status parses to nothing rather than to `unknown`: "we did
not understand the answer" and "the register says it does not know" are
different facts, and only the second is the register's.

Install `partner_autocomplete_orsf_sk`. It fills the register coordinates,
the status, the dissolution date and the check timestamp on every enrichment —
by feature detection, so neither module depends on the other.
