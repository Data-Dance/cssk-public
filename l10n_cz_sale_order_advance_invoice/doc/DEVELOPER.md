# l10n_cz_sale_order_advance_invoice: developer notes

Not user documentation: this file is not rendered into a page.

## Hook

- Creates the reconcilable advance-clearing account **324001** (Přijaté zálohy –
  zúčtování / daňový doklad) — the standard Czech chart has no reconcilable
  clearing account, so this module ships one.
* Wires the short-term received-advance account **324000** (Přijaté provozní
  zálohy) and the long-term received-advance account **475000** (Dlouhodobé
  přijaté zálohy).
* Sets up the tax-documents journal **TDADV** (Daňové doklady k přijatým
  platbám) for the tax document issued on a received payment.
* Idempotent post-install hook: only empty fields are filled, so manual
  configuration is never overwritten.
