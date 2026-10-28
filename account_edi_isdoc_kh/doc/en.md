---
title: ISDOC — Domestic Reverse Charge
summary: Czech invoices in the domestic reverse charge (§ 92a ZDPH) go out in ISDOC marked as such, with the commodity code the control statement reports.
verified: 19.0.1.0.0
family: account_edi_isdoc#reverse-charge
---

## What it does {#purpose}

In the Czech domestic reverse charge the customer, not you, pays the VAT
([§ 92a ZDPH](law:cz/2004/235#p92a)), and both of you report the supply in
the control statement with its **commodity code** (*kód předmětu plnění*) —
you in section A.1, the customer in B.1. ISDOC 6.0.2 has elements for
exactly this, which
[module:account_edi_isdoc](module:account_edi_isdoc) alone does not write.
With this add-on, every exported customer invoice or credit note line in the
reverse charge gets:

| ISDOC | Value |
|---|---|
| ClassifiedTaxCategory / LocalReverseCharge / LocalReverseChargeCode | the commodity code, e.g. `4` construction and assembly work |
| ClassifiedTaxCategory / VATApplicable | `true` — the supply is taxable, only the customer pays the tax |
| TaxSubTotal / TaxCategory / LocalReverseChargeFlag | `true` on its own VAT breakdown row, kept apart from exempt supplies that are also at 0 % |

The rate and the VAT stay at 0: an invoice in the reverse charge does not
have to state them ([§ 29 odst. 3 písm. e)](law:cz/2004/235)), and the
customer works the tax out itself. The document's *VATApplicable* is `true`
even when every line is in the reverse charge.

## Which lines {#lines}

The same lines the control statement
([module:l10n_cz_kh](module:l10n_cz_kh)) puts in section A.1: a line with a
tax marked as reverse charge, or with the chart's *0% RC* sale tax (row 25
of the VAT return).

The commodity code is also the control statement's: the **KH commodity code
(§92a)** of the product, or failing that of the reverse-charge tax (a tax
marked as reverse charge). It is written as the control statement's code
list defines it. ISDOC's own list predates it and numbers emission
allowances `2`; the control statement numbers them `11`, and that is what is
written, because the customer files the code in B.1.

## When the code is missing {#missing-code}

A reverse-charge line without a commodity code cannot be exported: the Send
dialog reports *"These reverse-charge lines have no KH commodity code"* and
names them. Set the code on the product (or on a reverse-charge tax) and send
again. The control statement refuses such a line too.

It installs itself when [module:account_edi_isdoc](module:account_edi_isdoc)
and [module:l10n_cz_kh](module:l10n_cz_kh) are both installed.

## Limitations {#limitations}

- Only customer invoices and credit notes. A proforma from a sales order
  ([module:account_edi_isdoc_sale](module:account_edi_isdoc_sale)) is not a
  tax document and carries no reverse-charge marking.
- *LocalReverseChargeQuantity* (the quantity in the unit of the commodity)
  is not written; the control statement does not report it.
- On import, a reverse-charge line at 0 % — as this add-on writes it — finds
  no reverse-charge purchase tax at that rate, so the line is left without
  tax and the bill's chatter says so ([receiving](module:account_edi_isdoc#import)).
  Choose the rate on the bill.
