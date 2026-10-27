---
title: Related Parties from the Slovak Registers (ORSF)
summary: Fetches one partner's officers and corporate shareholders, and the other companies they are linked to, from ORSF — a shortlist for identifying závislé osoby (related parties) under the Slovak Income Tax Act.
verified: 19.0.2.1.0
---

## What it is for {#purpose}

Prices between **závislé osoby** (related parties) must be at arm's length, and
nothing in an Odoo database knows which of your partners are related to you or
to each other. ORSF's ownership and officer graph answers part of the question
mechanically: who holds a role in a company, and in which other companies the
same people hold roles.

This module adds a tab to a Slovak contact that fetches that graph for one
partner on request and lists what it found — including companies that are not
contacts in your database.

## Legal background {#legal}

References are to the
[zákon o dani z príjmov](law:sk/2003/595).

- **Who is a závislá osoba.** [§ 2 písm. n)](law:sk/2003/595#paragraf-2.pismeno-n):
  a close person, an economically, personally or otherwise connected person or
  entity, or a member of the same consolidated group.
  [§ 2 písm. o)](law:sk/2003/595#paragraf-2.pismeno-o) defines economic and
  personal connection: a share of at least 25 % in capital, voting rights or
  profit, and — for personal connection — membership of the statutory,
  supervisory or similar bodies of a legal entity, including entities under the
  control or management of the same person.
- **What follows from it.** [§ 17 ods. 5](law:sk/2003/595#paragraf-17.odsek-5):
  the tax base of a závislá osoba includes the difference by which prices or
  conditions in significant controlled transactions differ from those
  independent parties would use, where that difference lowers the tax base or
  raises the tax loss.
- **Documentation.** [§ 18 ods. 1](law:sk/2003/595#paragraf-18.odsek-1): the
  taxpayer must keep documentation of controlled transactions and the pricing
  method used.

The register shows only part of the test. It does show shared officers, the
personal connection that the graph is built from. It does not show close
persons, most shareholdings below the officer level, or "other connection".
**Treat the list as a shortlist for your accountant, never as the conclusion.**

## Setting it up {#setup}

ORSF serves the ownership graph only to a signed-in account and issues no API
key for it. In *Settings → General Settings → Contacts*, with **ORSF.SK** as the
provider (see [module:partner_autocomplete_orsf_sk](module:partner_autocomplete_orsf_sk)),
fill **ORSF account e-mail** and **ORSF account password**. The session is
obtained and renewed automatically.

The password is stored **in plain text** in the database and in every backup.
Use a dedicated ORSF account, never a personal one. The signed-in session is
used only for this graph request; autocomplete and lookups stay anonymous.

## Fetching related parties {#usage}

1. Open a contact. It needs an IČO in *Company ID* (or from an earlier
   autocomplete).
2. Tab **Related parties (SK)** — shown for contacts in Slovakia or with no
   country.
3. Press **Fetch from register**. Anybody who may edit the contact can do it.

The previous list is replaced by what the register says now, and the time of
the fetch is shown next to the explanation. Each row:

| Column | Meaning |
|---|---|
| Degree | **1** — a natural person or a company holding a role directly in this partner, such as a konateľ or a corporate spoločník. **2** — another company that person or company is also linked to. |
| Name, IČO | the person (degree 1, no IČO), the company holding the role (degree 1, with IČO) or the other company (degree 2) |
| Through | the person — or, for a corporate shareholder, the company — linking the two; empty on a degree-1 company |
| Role | the role as the register words it — konateľ, spoločník, člen predstavenstva |
| Related contact | the contact in your database with that IČO in *Company ID*, if there is one |

The list is read-only on the contact. The arrow at the end of a row opens the
related contact, when there is one, and the **Register links** button at the
top of the contact opens the list on its own.

The Slovak screen labels say **Väzby v registri** (register links), not
*závislé osoby*: a link in the register is a lead, and only the statutory test
above makes it a závislá osoba.

**One partner at a time, deliberately.** ORSF serves the graph on the condition
that callers do not bulk-fetch persons (it cites legitimate interest under
Art. 6(1)(f) GDPR). There is no batch action, no scheduled job and no
multi-record selection, and there will not be one.

## Limitations {#limitations}

- ORSF does not publish the format of the graph. The module reads the usual
  graph formats and skips anything it does not recognise, so a format change
  shows up as fewer rows, not wrong ones. Check a few partners against the
  register before relying on the list.
- Degree 2 is as far as it goes: companies of the people in this partner, not
  companies of the people in those companies.
- Natural persons are recognised by having no IČO; anything with an IČO is
  treated as a company.
- A failed sign-in, an expired session or a rate limit is reported as "ORSF
  returned no graph"; the server log has the cause.
