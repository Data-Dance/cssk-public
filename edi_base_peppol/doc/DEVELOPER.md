# edi_base_peppol: developer notes

Not user documentation: this file is not rendered into a page.

## Provider hooks

- `_peppol_provider()` — the provider key stamped on the outbound
  `edi.message` (`doc_family='peppol'`);
* `_peppol_send(msg)` — enqueue that message via the provider's connector.

This module deliberately does **not** use Odoo's `account_peppol` /
`account_peppol_response`, whose send/receive path is hard-wired to Odoo's
own SAS access point.
