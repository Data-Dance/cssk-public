---
title: CZ/SK Company Registry Verification
summary: Checks against the Czech or Slovak business register whether an IČO belongs to an existing, active company, and keeps the answers in a short-lived cache.
verified: 19.0.1.0.0
---

## What it is for {#purpose}

A well-formed IČO — one that passes its check digit — is not yet a company. This
module answers the next question: **does the company exist in the state
register, and is it still active?** It has no button of its own. Other modules
ask it before they act on an IČO; for example
[module:l10n_cssk_receipt_capture_ai](module:l10n_cssk_receipt_capture_ai)
takes a seller's official name from the register by the IČO read from a receipt.

Every check ends in one of five answers:

| Answer | Meaning |
|---|---|
| Not a valid company number | fails the check digit; the register is not asked |
| No register for this country | not a Czech or Slovak number, or the provider module for that country is not installed |
| Not in the register | the register answered and holds no such subject |
| Verified | the register answered with the company: name, address, DIČ, the VAT number while its VAT registration is live, and whether it is active |
| Register unreachable | outage, timeout or rate limit — nobody knows whether the company exists |

The last two are kept strictly apart. Each module that uses the check decides
for itself what to do when the register cannot be reached; it never reads an
outage as "the company does not exist".

When a company name is supplied, the register's name is compared with it and the
result is *Matches the register*, *Close, needs a look* or *Does not match*.

## Setting it up {#setup}

The registers are read through the partner-autocomplete providers, which this
module finds at run time but does not install:

- Slovakia — [module:partner_autocomplete_orsf_sk](module:partner_autocomplete_orsf_sk) (ORSF);
- Czech Republic — [module:partner_autocomplete_ares_cz](module:partner_autocomplete_ares_cz) (ARES).

Install the one for each country you need. Nothing else has to be configured.

## Cached answers {#cache}

*Accounting → Configuration → CZ/SK Localization → Register lookups* lists the
answers kept, newest first: when, country, IČO, the name in the register, the
answer, whether the company is active and which register answered. Filters:
*Verified*, *Not in the register*, *Dissolved*; group by country or answer.

- A *Verified* answer is reused for 24 hours, a *Not in the register* answer
  for one hour — a company that does not exist today may be incorporated
  tomorrow.
- *Register unreachable* is never cached, so the next check asks again.
- The list is read-only for users; administrators can delete a row to force a
  fresh check.

The lifetimes can be changed with the system parameters
`l10n_cssk_registry_verify.ttl_verified_hours` and
`l10n_cssk_registry_verify.ttl_absent_hours` (0 disables caching).

## Limitations {#limitations}

- Only Czech and Slovak IČOs. A partner from any other country is always
  *No register for this country*.
- A cached answer can be up to a day old: a company dissolved this morning may
  still show as active.
- ARES has no status field; a Czech company counts as active when it has no
  date of dissolution.
- The verification fields this module adds to contacts are not shown on any
  screen.
- The screen labels are not translated.
