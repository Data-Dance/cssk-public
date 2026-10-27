---
title: CZ Statutory Reference Data
summary: The Czech tax offices, taxpayer types and filer details that every Czech electronic filing (EPO) needs, and the bad-debt correction flag on invoices.
verified: 19.0.1.3.0
---

## What it is for {#purpose}

Every Czech filing sent through the tax administration's EPO portal — the VAT
return (DPHDP3), the control statement (*kontrolní hlášení*), the EC sales
list (*souhrnné hlášení*), the corporate income tax return (DPPO) — carries
the same header: which tax office it goes to, who the taxpayer is, who signs
it and who prepared it. This module supplies that data once, for all of
those forms:

- **the Czech tax offices** (*finanční úřady*) with their codes;
- **the taxpayer types** *Fyzická osoba* (natural person) and *Právnická
  osoba* (legal entity);
- **the filer details** on the company: the authorised signatory, who
  prepared the filing, and a representative such as a tax adviser;
- a **check before export** that the company's tax office can be filed;
- the **bad-debt correction flag** on invoices and credit notes, which the
  VAT return and the control statement read.

It also installs `partner_nace`, from which the VAT return and the DPPO take
the company's main economic activity (NACE code).

The registers themselves (*Tax Authorities*, *Person / Entity Types*) come
from [module:l10n_cssk_core](module:l10n_cssk_core); this module fills them
with Czech data so that none of it loads on a Slovak database.

## Legal background {#legal}

- **Bad-debt correction.** A creditor may correct the tax base when a
  receivable becomes unrecoverable under the conditions of
  [§ 46 and following of the VAT Act](law:cz/2004/235) (enforcement or
  insolvency proceedings, among others). A debtor who is a VAT payer must
  then reduce the input tax it deducted —
  [§ 74b of the VAT Act](law:cz/2004/235). Neither is an ordinary credit
  note: the VAT return reports them on separate rows and the control
  statement lists them whatever their amount, which is why the document has
  to say so.

## Setting it up {#setup}

**Company.** *Settings → Users & Companies → Companies*, open the company:

| Field | What to enter |
|---|---|
| Tax Authority (*Finanční úřad*) | The **regional** tax office the company files to, e.g. *Finanční úřad pro Jihomoravský kraj*. Its code is filed as `c_ufo`. |
| Tax Office (CZ) (*Finanční Úřad (CZ)*) | Odoo's own field: the **territorial workplace** (*územní pracoviště*). Its code is filed as `c_pracufo`. Optional. |
| Entity Type (*Typ subjektu*) | *Právnická osoba* or *Fyzická osoba*. Decides whether filings are made as a legal entity (`typ_ds` P) or a natural person (F). Empty counts as a legal entity. |
| NACE (main activity) | On the company's contact; filed as the activity code. |

Both tax-office fields show as *Finanční úřad* in Czech, which is easy to
mix up: the first is the regional office, the second the workplace. The
default tax office can also be set under *Accounting → Configuration →
Settings*, block *Czech / Slovak Localization*, field *Default tax authority*.

**Page *EPO podání*** on the company form, shown only for Czech companies.
The labels are in Czech in every language:

| Group | Fields | When |
|---|---|---|
| Fyzická osoba | Titul, Jméno, Příjmení | the company is a natural person |
| Oprávněná osoba | jméno, příjmení, vztah k právnické osobě (e.g. *jednatel*) | the company is a legal entity |
| Sestavil | jméno, příjmení, telefon | who prepared the filing |
| Zástupce | Zástupce, Typ zástupce, Evidenční číslo zástupce, Datum narození zástupce | someone files on the company's behalf |

The address, telephone and e-mail in the filings come from the company's own
contact details. The street is split into street name, *číslo popisné* and
*číslo orientační* (from `Street 1141/11`); a street that does not end in a
number is filed whole, without a house number.

For a **representative**, choose the contact and the *Typ zástupce* (required
once a representative is set), from the EPO code list — for example *4b –
daňový poradce nebo advokát (fyzická osoba)* or *4c – právnická osoba
vykonávající daňové poradenství*. A company contact is filed as a legal
entity with its name and IČO (*Company ID*); a person is filed as a natural
person, the name split at the last space into first name and surname, and
needs either the *Evidenční číslo zástupce* (for a tax adviser, the Chamber
of Tax Advisers number) or the date of birth.

**Tax offices.** *Accounting → Configuration → CZ/SK Localization → Tax
Authorities* lists the 14 regional offices and the *Specializovaný finanční
úřad*, with addresses, and under each regional office its territorial
workplaces. The codes come from Odoo's official Czech tax office list, so a
new office appears there when Odoo updates that list. Installing or upgrading
the module adds missing offices and never overwrites ones you edited.

## Before export: the tax office check {#export-check}

When a Czech filing is exported, the company's tax office is checked first,
and the export stops with an explanation if:

- no tax office is set on the company;
- the tax office is not a Czech one;
- the office has no *Submission Code* (*Kód podání*);
- the code has more than three digits — typically because a territorial
  workplace was chosen instead of the regional office; the message then names
  the regional office to choose.

The check applies to companies whose fiscal country is the Czech Republic,
and not to the OSS return, which carries no tax office.

## Bad-debt corrections on invoices {#bad-debt}

On a customer or vendor invoice or credit note of a Czech company, tab
*Další informace*, the field **Oprava u nedobytné pohledávky** marks a
correction of tax on an unrecoverable receivable:

| Value | Use |
|---|---|
| Oprava u nedobytné pohledávky (§ 46 / § 74b) | the creditor's correction (§ 46 and following) or the debtor's (§ 74b) |
| Oprava podle § 44 ve znění do 31. 3. 2019 | the old § 44 procedure, only for supplies made up to 31 March 2019 |

Use the ordinary taxes on the document; the flag is what moves it to the
right rows. With [module:l10n_cz_vat_return](module:l10n_cz_vat_return) the
tax goes to row 33 (creditor) or row 34 (debtor) of the VAT return instead of
the ordinary rows, and with [module:l10n_cz_kh](module:l10n_cz_kh) the
document is reported in section A.4 or B.2 of the control statement whatever
its amount.

The field can be changed only while the document is a draft, and changes are
logged in the chatter. Odoo refuses the old § 44 value when the corrected
invoice (the one the credit note reverses) is dated after 31 March 2019, and
refuses the flag altogether on a company that does not file Czech VAT.

## Limitations {#limitations}

- The tax office addresses are included for convenience and are not
  maintained automatically; check them if you print them.
- A natural-person representative's name is split at the last space, so a
  double surname must be checked in the filing.
- The house number is split only from a street that ends in a number.
- The VAT payer type in the VAT return is always *plátce* (P) unless
  [module:l10n_cz_vat_status](module:l10n_cz_vat_status) records otherwise.
- The bad-debt flag does not check the § 46 conditions themselves (time
  limits, proceedings); it only records which procedure the document follows.
