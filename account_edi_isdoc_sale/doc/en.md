---
title: ISDOC — Proformas from Sales Orders
summary: Downloads a sales order as an ISDOC proforma (document type 4, a request for an advance payment) from the order's Action menu.
verified: 19.0.1.1.0
family: account_edi_isdoc#proforma
---

Adds the export of a sales order as an ISDOC 6.0.2 **proforma**, document type 4 (*zálohová faktura*): order number, order date, lines, totals, and the company's first bank account with the order number's digits as variable symbol. The UUID is kept on the order, so a repeated export carries the same identity. On the order, **Action → Download ISDOC Proforma** downloads it as `S00042.isdoc` and keeps it as the order's attachment, replaced on every download so it always matches the order as it stands. A cancelled order cannot be exported, and missing names or addresses of your company or the customer are listed instead of a file. Integrations can call the same export directly.

It installs itself when [module:account_edi_isdoc](module:account_edi_isdoc) and Sales are both installed, and has no settings.
