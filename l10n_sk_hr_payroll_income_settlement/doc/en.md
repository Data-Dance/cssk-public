---
title: Additional-income tax and health calculation
summary: Reviewed monthly cash settlement from historical social premiums and dated tax/health parameters, before native payroll integration.
verified: 19.0.1.0.1
---

## Purpose {#purpose}

Calculate reviewed positive cash remuneration after termination. Social
premiums come from the historical register; health and income tax use the
reviewed reporting month and native dated parameters. Other monthly payments
are consolidated before applying tax bands/NČZD. The one-day 2Y health profile
supports minimum top-ups and refund of a previous monthly top-up.

Editable form fields and optional hidden API facts cannot be mixed. Evidence,
source/parameter digests, archived calculations, retries and reset dependencies
are checked. The calculation stores amounts, not an accounting entry.

## Limits {#scope}

Monthly cash settlement paid in the next month of the same year, insurance
ended before that reporting month, only one 2Y health day; no child bonus,
other benefits/deductions or exceptional corrections. Health profiles and tax
pension status are separate reviewed facts. Native slip/accounting integration
belongs to the separate native payroll bridge; historical VPP/health exports remain separate.
