=========
Changelog
=========

All notable changes to **l10n_sk_ubl_bis3** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.1.1] — 2026-09-13
-------------------------

Fixed
~~~~~

- Slovak catalogue completed. Terms already stated in Slovak in the
  source are deliberately left untranslated — the source IS the
  translation, per the hybrid convention for these modules.

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.1.0] — 2026-07-14
-------------------------

Changed
~~~~~~~

- ``cbc:PaymentID`` (BT-83) now prefers the canonical
  ``l10n_cssk_variable_symbol`` when ``l10n_cssk_payment_symbols`` is
  installed, falling back to the previous payment_reference/name digits.

[19.0.1.0.0] - 2026-06-16
-------------------------

Added
~~~~~

- Initial release. Registers the Peppol BIS Billing 3.0 format for Slovakia
  (``ubl_bis3_sk``), since ``SK`` is absent from Odoo core's
  ``PEPPOL_DEFAULT_COUNTRIES`` and is therefore not auto-suggested otherwise.
- ``account.edi.xml.ubl_sk`` builder (thin subclass of ``account.edi.xml.ubl_bis3``)
  as a stable extension point. No CustomizationID deviation — Slovakia has no
  national billing CIUS.
- Slovak *variabilný symbol* (VS) mapped onto ``cac:PaymentMeans/cbc:PaymentID``
  (BT-83).
- Auto-default of ``invoice_edi_format`` for Slovak partners.
- Tests covering format registration, builder mapping, auto-suggestion, and
  export content (CustomizationID, IČ DPH, IBAN, VS).

19.0.3.1.0 (2026-10-03)
=======================

* **The 9950 → 0245 move is now re-runnable**,
  ``res.partner.action_l10n_sk_adopt_dic_participant``, and the 19.0.2.0.0
  migration calls it instead of carrying its own copy.

  It had to be. The migration fires at upgrade, which is *before* anyone has
  recorded the DIČs it requires, so it legitimately skips almost everything.
  The DIČs are then recorded — ``partner_autocomplete_orsf_sk`` has
  ``action_orsf_fill_missing_dic`` — and nothing re-runs the move, because
  ``_compute_peppol_eas`` will not promote a partner off ``9950``: that is a
  valid Slovak code, so core's rule treats it as a scheme somebody chose, and
  this module preserves that.

  The behaviour is reproducible on a clean database: create a Slovak partner
  with a VAT number and no DIČ (it computes to ``9950``), record the DIČ
  afterwards, and it stays on ``9950`` through ``flush_all`` and
  ``invalidate_all``. The export constraint cannot catch that, because the DIČ
  is present — so it is a wrong identifier, silently, by a different route than
  the one 3653b4a7 closed.

  Honesty about the scale: a run on a copy of ``19CE-I6-CLEAN`` appeared to
  leave 1003 partners in that state, and an earlier draft of this entry said so.
  Re-reading the same database afterwards showed them on ``0245``, with no
  migration and no adoption call in any log, and the transition could not be
  reproduced on a clean database. The original state has since been
  overwritten, so the mechanism is unexplained and that figure is **not**
  evidence of anything. What justifies this action is the reproducible
  single-record behaviour above, plus the ordering: the migration fires at
  upgrade, before the DIČs it needs exist.

  Conservative about overwriting: a partner is moved only if its endpoint is
  empty or is exactly what core derived from the VAT number. A hand-typed
  endpoint is somebody's deliberate registration, and is left alone and logged.

19.0.3.0.1 (2026-10-03)
=======================

* **The export constraint was gated on the wrong thing and caught about a tenth
  of what it should.** 19.0.3.0.0 refused a Slovak party only when
  ``peppol_eas == '0245'`` and no DIČ was recorded. But with no DIČ recorded
  ``_compute_peppol_eas`` never promotes the partner to ``0245`` in the first
  place — it keeps core's ``9950`` default — so the common case walked straight
  past the check and exported under the IČ DPH: wrong, but well formed, so
  nothing complained anywhere.

  Measured on ``19CE-I6-CLEAN`` (RF Elements i6 rebuild, real partner data):
  of 1204 Slovak trading partners with no DIČ, **1076 sat on 9950 and 127 on
  0245**. The old gate saw the 127.

  Now gated on the missing DIČ alone. A partner deliberately published under
  another scheme still passes as long as its DIČ is on file — the constraint
  asks for the number, not for a particular scheme, so a live 9950 registration
  is not broken by it.

19.0.3.0.0 (2026-09-26)
=======================

* **The DIČ is no longer derived from the VAT number.** 19.0.2.0.0 filled the
  ``0245`` endpoint from ``vat`` minus its ``SK`` prefix when no DIČ was
  recorded, on the premise that an IČ DPH simply *is* ``SK`` + the DIČ, so no
  existing database would need data entered. Withdrawn: the cost of that
  premise being wrong is not a blank field but a participant identifier
  belonging to somebody else.

  It is already wrong in one place we can point at. The ePošťák sandbox firms
  carry a **synthetic** IČ DPH, because their real DIČ fails ``base_vat``'s SK
  checksum and the nearest valid number was substituted — so deriving gives
  ``4536197523`` where the participant is ``4536197514``, and on that database
  the derivation would have overwritten a hand-set, working identifier with a
  wrong one. Whether real subjects diverge as well — VAT groups under § 4b,
  § 5 non-resident registrations, legacy numbering — is **an open question and
  is now assumed possible** rather than assumed away.

  Consequences, all deliberate:

  - A partner with no recorded DIČ gets **no** ``0245`` endpoint, and keeps
    whatever scheme core computes. It is not given a fabricated one.
  - ``_l10n_sk_peppol_constraints`` refuses the export, naming the party, so the
    failure lands at export with something actionable rather than at the access
    point — where an unknown participant is reported as a *validation* error and
    reads as a malformed payload.
  - The 19.0.2.0.0 migration now skips any partner without a recorded DIČ, and
    logs each one. On most databases that log **is** the list of contacts whose
    DIČ has to be entered before they can be e-invoiced. Budget for that ahead
    of January 2027; it is data entry, not a code change.

* ``19.0.3.0.0``: removes a capability. Endpoints already stored are untouched,
  but partners that would previously have been given a derived one now need the
  DIČ recorded.

* Note for whoever audits this: ``account_invoice_ai_extract`` makes the same
  ``vat[2:]`` assumption at ``models/ai_extraction.py:216``, independently and
  predating this module. It is left alone — there the derived value is a
  best-effort hint for matching a supplier on an extracted invoice, not a
  statutory identifier published on a network — but if the § 4b answer ever
  comes back "they diverge", that site wants revisiting too.

19.0.2.0.0 (2026-09-16)
=======================

* **Slovak partners are now identified as ``0245:<DIČ>``.** Core 19.0 has
  ``'SK': {'9950': 'vat', '0245': 'company_registry'}``
  (``account_edi_ubl_cii/models/account_edi_common.py:100``), which is wrong
  twice. ``_compute_peppol_eas`` walks that mapping in dict order and takes the
  first field holding a value, so a VAT payer went out as
  ``9950:SK2020317068``; and the ``0245`` fallback was filled from
  ``company_registry`` — the eight-digit **IČO** — under a code whose own
  selection label reads "SK Tax identification number (DIČ)". The Slovak
  participant identifier is the ten-digit DIČ. An access point answers an
  unknown participant with a *validation* error rather than a "not found", so
  the wrong scheme reads as a malformed request and costs an hour before anyone
  suspects the identifier.

  Fixed by overriding ``_compute_peppol_eas`` and ``_get_peppol_endpoint_value``,
  **not** by re-ordering ``EAS_MAPPING['SK']``. That dict is a module-global and
  Python imports it once per *process*, so editing it would reach every database
  the worker serves — including ones where this module is not installed, whose
  registries carry none of these overrides. A localisation must not change how
  another database identifies its partners. The core mapping is left exactly as
  it is, which also keeps ``9950 -> vat`` intact for the **import** side, which
  scans it for the entry whose field is ``'vat'`` to recover a supplier's VAT
  from an inbound ``PartyIdentification`` (``account_edi_ubl.py:2679``,
  ``account_edi_xml_ubl_20.py:1119``).

  The override preserves core's own rule that a scheme somebody chose
  deliberately survives: core recomputes only when the stored value is not
  already valid for the country, and the set eligible to change is taken before
  ``super()`` using exactly that test. It moves defaults, never choices. It also
  refuses to flip the scheme when no DIČ is derivable, because
  ``_compute_peppol_endpoint`` keeps the previous endpoint when the new one is
  empty — which would leave an IČ DPH sitting there labelled as a DIČ.

  Where no DIČ is recorded the number is derived from the VAT number, since
  IČ DPH *is* ``SK`` + the DIČ — so an existing database needs nothing
  re-entered. A subject registered for income tax but not for VAT has no IČ DPH
  at all, and there the stored DIČ is the only source; that is the case the
  field exists for. New dependency on ``l10n_sk_base``, which owns it.

  Odoo agrees on the direction: `PR #275798
  <https://github.com/odoo/odoo/pull/275798>`_ reorders the same mapping to put
  ``0245`` first, with a ``TODO`` to point it at the DIČ once `PR #280178
  <https://github.com/odoo/odoo/pull/280178>`_ lands. Both are still open —
  neither has moved since August — and the mandate is January 2027.

* **``sequence`` lowered from 200 to 150.** Today ``SK`` is absent from
  ``PEPPOL_DEFAULT_COUNTRIES``, so ``ubl_bis3_sk`` is the only format offered
  for Slovakia and wins by being alone. PR #275798 adds ``SK`` to that list, at
  which point ``_get_suggested_ubl_cii_edi_format`` picks ``min()`` by sequence
  over ``['ubl_bis3', 'ubl_bis3_sk']`` — and at equal sequences the tie breaks
  on dict order, handing Slovak invoices to the generic builder and silently
  dropping the *variabilný symbol* → ``cbc:PaymentID`` (BT-83) mapping on the
  ``_get_suggested_peppol_edi_format`` path that ``edi_base_peppol`` uses. The
  existing ``_get_suggested_invoice_edi_format`` override is not on that path.

* **A migration moves existing partners.** Because the compute leaves a valid
  stored EAS alone, every Slovak partner already carrying ``9950`` would have
  kept it — and almost all of them carry it because core *defaulted* them there,
  not because anyone chose it. ``migrations/19.0.2.0.0/post-migrate.py`` moves
  them once, and only where it is safe: Slovak, currently ``9950``, a DIČ
  derivable, and an endpoint that still matches what core derived from the VAT
  number. A partner whose endpoint was typed by hand is left alone — that is a
  deliberate registration and a migration has no business overruling it. Every
  skip is logged with its id and the reason, so the set needing a human is a
  grep rather than a guess.

* ``19.0.2.0.0``: the participant identifier published for Slovak partners
  changes. Anything deliberately registered under another scheme, or carrying a
  hand-set endpoint, is left where it is.

