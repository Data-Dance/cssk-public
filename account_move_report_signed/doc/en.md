---
title: Signed Amounts on Credit Notes (PDF)
summary: Prints the amounts on a customer credit note as negative numbers, the way Czech and Slovak readers expect a credit note to look.
verified: 19.0.1.0.1
---

## What it is for {#purpose}

Odoo prints a customer credit note with positive amounts and relies on the
title to say that the money goes the other way. Czech and Slovak accountants
and customers expect a credit note (*dobropis*, *opravný daňový doklad*) to
show the reduction as **negative** amounts. This module changes the printed
document accordingly. It changes nothing in the accounting.

## What changes on the PDF {#usage}

On a **customer credit note**, these values are printed with a minus sign:

- the unit price, and the subtotal (or total, if your prices include tax) of
  each line;
- the subtotal of each section;
- lines grouped on the document;
- the totals block: the tax base, the tax per tax group and the total, also
  in the company currency when the credit note is in a foreign currency.

Customer invoices, vendor bills and **vendor credit notes** keep their signs.
The amount due, the list of payments and the payment QR code are not
changed. There is nothing to configure: install the module and print.

## Limitations {#limitations}

- Only customer credit notes are affected; vendor credit notes printed from
  Odoo stay positive.
- The negative unit price is the module's choice of presentation: the
  quantity stays positive.
