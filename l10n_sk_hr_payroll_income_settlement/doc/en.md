---
title: Additional-income tax and health calculation
summary: Reviewed monthly cash settlement from historical social premiums and dated tax/health parameters, before native payroll integration.
verified: 19.0.1.0.2
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

## Legal basis {#legal-basis}

Monthly tax consolidation follows [§ 35](law:sk/2003/595#paragraf-35), declaration
facts [§ 36](law:sk/2003/595#paragraf-36), and cent rounding [§ 47](law:sk/2003/595#paragraf-47).
The pension status at 1 January under [§11(6)](law:sk/2003/595#paragraf-11.odsek-6)
does not grant a monthly allowance merely because the declaration checkbox is
selected. Finančná správa's [2026 NČZD FAQ, questions 7 and 9](https://podpora.financnasprava.sk/260857-Nezdanite%C4%BEn%C3%A1-%C4%8Das%C5%A5-z%C3%A1kladu-dane-na-da%C5%88ovn%C3%ADka-za-rok-2026)
explicitly excludes monthly NČZD for that pension profile, including a small
pension; the difference after annual pension including the 13th pension belongs
to annual reconciliation/personal return. A pension first effective later in
the year is a different tax fact. The 2027 §35 wording retains that distinction.

Health scope/exclusions follow [§ 10b](law:sk/2004/580#paragraf-10b) and
[§11(3)](law:sk/2004/580#paragraf-11.odsek-3), rates and monthly advances
[§ 16](law:sk/2004/580#paragraf-16), and the day-proportional minimum, its exceptions
and additional employee advance [§ 16a](law:sk/2004/580#paragraf-16a).
The 2Y code and last-day, single-day registration follow insurer methodology,
not a literal code in the statute: [Union instructions](https://www.union.sk/pomoc-a-podpora/nepravidelny-prijem-a-prijem-vyplateny-zamestnancovi-po-skonceni-pracovneho-pomeru/).
If an earlier payment of the same month already charged a minimum top-up, the
new calculation pays only the difference from the consolidated monthly amount;
a negative difference returns the earlier excess. It is not an annual-insurer
refund or permission to refund an unrelated period's contribution.
