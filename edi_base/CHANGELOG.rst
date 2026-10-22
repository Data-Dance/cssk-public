=========
Changelog
=========

All notable changes to **edi_base** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[18.0.1.5.0] — 2026-08-23
-------------------------

Changed
~~~~~~~

- Back-ported from the 19.0 branch (``odoo-modules-playground``).
- **19 → 18 delta:** ``models/res_partner.py`` imported the core class as
  ``ResPartner``. Odoo 19 renamed the core model classes to match their model
  names (``Partner`` → ``ResPartner``); on 18.0 the class is still ``Partner``,
  and the 19.0 name fails at *import* time with a bare ``ImportError`` that
  aborts the whole registry load. Now imports ``Partner``.
- ``_sql_constraints`` is kept as-is: it is native on 18.0 (19.0 only warns
  about it in favour of ``models.Constraint``).
- ``<chatter/>`` is kept as-is — it is valid on 18.0, not a 19.0-only element.


[19.0.1.5.0] — 2026-08-22
-------------------------

- **Add ``edi.message._write_outside_job(vals)``** — persist a record write on
  a fresh cursor so it survives what queue_job does on a job failure. The
  obvious "record the outcome, then raise" pattern loses the write entirely:
  ``_runjob`` calls ``env.cr.rollback()`` on the RetryableJobError branch and
  re-raises to the http layer (which rolls back too) on FailedJobError, while
  ``_try_perform_job`` wraps ``perform()`` in ``_prevent_commit`` so the job
  cursor cannot be committed instead. The helper rolls back first — releasing
  the row locks a second cursor would otherwise deadlock against — then writes
  and commits separately, and never raises, since it is bookkeeping for a
  failure that is already propagating.

  *Verified against a real database in a non-test process*: the value written
  through the helper survived a subsequent ``cr.rollback()`` and was visible to
  a separate process, while an inline ``write()`` on the same record did not.
  Odoo forbids commit/rollback of a cursor taken inside a test, so the durable
  path cannot be covered by a ``TransactionCase`` — only the guard logic is.

[19.0.1.4.1] — 2026-08-06
-------------------------

- **Fix**: ``_get_effective_type`` returned the wrong dispatch type
  for COMDIS (and would do the same for APERAK) because it mapped
  ``doc_type_code`` through ``DOC_TYPE_MAP`` first — but the
  ``<document_type>`` in a COMDIS body refers to the *disputed*
  document (e.g. 380 = the invoice being disputed), not to what
  this message is. So every inbound COMDIS resolved to ``INVOIC``
  and the sale-side dispatcher skipped it (guard: ``etype not in
  ("ORDERS", "RECADV", "COMDIS")``). ``_process_comdis`` never
  ran, and ``edi_dispute_state`` on invoices was never set.
  Add ``META_MESSAGE_TYPES = {"COMDIS", "APERAK"}`` — for these,
  trust ``message_type`` verbatim and skip the DOC_TYPE_MAP
  override.

[19.0.1.4.0] — 2026-07-15
-------------------------

- **Add**: ``edi.message._inbound_dispatch_may_commit()`` hook (default
  ``False``) and a commit-tolerant branch in ``_poll_provider`` phase 2.
  Some document-family importers COMMIT the cursor mid-dispatch — notably
  Peppol UBL, where Odoo core ``account_document_import_mixin`` wraps the
  decode in ``rollbackable_transaction``, which commits. That released the
  wrapping ``cr.savepoint()`` and raised ``InvalidSavepointSpecification`` on
  RELEASE, poisoning the whole inbound-poll batch. Families that return
  ``True`` from the hook now persist the stub first, dispatch **without** a
  savepoint, and commit per message; a failure rolls back and marks the
  already-persisted stub ``error``. If the stub commit itself fails the
  interchange is left unacknowledged (re-fetched next poll) — no
  ack-without-persist data loss. **EDIFACT is unchanged** (hook stays
  ``False`` → original savepoint path). *Live-validated* against Editel eXite;
  reviewed via GPT-5.3-codex.

[19.0.1.3.0] — 2026-07-08
-------------------------

- **Add**: ``edi.message.doc_family`` Selection (``_selection_doc_family``,
  default ``edifact``) — the *document standard* of a message, orthogonal to
  ``provider`` (= transport). Lets one provider mailbox carry several
  standards (e.g. Editel eXite carrying both EDIFACT and Peppol BIS3).
- **Add**: two overridable inbound-polling seams on ``edi.message`` so
  non-EDIFACT families can plug in without forking ``_poll_provider``:
  ``_dedup_key_for_inbound(connector, xml_content)`` (default = biztalk
  ``message_id``) and ``_inbound_stub_vals(provider, xml_content, pkg)``
  (default = the historical stub dict). Both defaults preserve existing
  Editel/GRiT behaviour exactly.

[19.0.1.2.1] — 2026-06-18
-------------------------

- **Change**: drop the dedicated *EDI auto-send overrides* notebook page.
  Provider modules now inject their Selection fields directly into the
  partner form's *misc* group right below the ``edi_auto_send_override``
  Boolean, gated by the same ``invisible="not edi_auto_send_override"``
  attribute. UI-only change — resolver logic, field names, and stored
  values are unchanged.

[19.0.1.2.0] — 2026-06-15
-------------------------

- **Add**: ``edi.message.customer_ref`` indexed Char — buyer's reference
  (sale-side) / vendor's reference (purchase-side). Lets a whole
  document conversation (ORDERS → ORDRSP → DESADV → INVOIC) be searched
  by the same counterparty reference. Shown in list view (optional),
  form view's *Provider correlation* group, and search view.
- **Add**: ``res.partner.edi_auto_send_override`` Boolean — when on,
  per-provider Selection fields (added by ``edi_editel_*``, ``edi_grit_*``)
  take precedence over the global ``ir.config_parameter`` auto-send flags
  for that commercial partner. New *EDI auto-send overrides* notebook
  page on the partner form, conditional on the Boolean.
- **Add**: ``res.partner._edi_resolve_auto_send(override_field_name, config_param)`` generic resolver. Reads the per-partner Selection
  override (``always`` / ``never`` / ``default``) and falls back to the
  global config parameter when off / ``default``.

[19.0.1.1.0] — 2026-06-05
-------------------------

- **Add**: ``res.partner.edi_communication_partner_id`` Many2one + cascading
  ``_edi_envelope_partner()`` helper. Lets multi-GLN customers (METRO etc.)
  model a separate eXite mailbox-owning partner; outbound BizTalk
  envelope ``<to>/<from>`` resolves through it while body party blocks use
  the role-specific partner's own GLN. Cascade is driven by
  ``commercial_partner_id`` so the field need only be set on the legal entity.
- **Add**: ``res.partner.edi_desadv_sscc_mode`` Boolean flag, cascading.
  Opt-in per customer (or per commercial root) for SSCC-mode DESADV
  emission. METRO and the other Slovak retailers consume this from the
  picking's emit helper.
- **Add**: edi.message bulk-send action (``Send (queue dispatch)`` on the
  list view) plus ``edi.message.send.wizard`` for the per-record /
  multi-record confirm dialog. Always-open wizard variant (no quick-queue
  fallback).
- **Add**: ``_backfill_partner_id_from_links()`` helper — resolves
  ``partner_id``, ``sale_order_id``, ``purchase_order_id`` from any linked
  business record (picking, invoice, payment) when they weren't set at
  parse/emit time.
- **Add**: Local-TZ helpers ``_edi_tz()``, ``_edi_combine_local_to_utc()``,
  ``_edi_now_local_split()``, ``_edi_dt_to_local_split()`` — used by all
  outbound emit helpers and the inbound ORDERS parser to stop UTC-
  mangling Slovak local times.
- **Add**: ``SENDABLE_STATES`` tuple + ``action_queue_send_selected()`` for
  the bulk-send wizard.
- **Fix**: ``_get_xml_content()`` falls back to cp1250 when strict UTF-8
  decode fails (some senders mis-declare cp1250 bytes as UTF-8).
- **Add**: ``UserError`` import (used by the bulk-send method).

[19.0.1.0.1] — 2026-06-05
-------------------------

- Manifest version bump (achulii) to force upgrade-time data reload.

[19.0.1.0.0] — initial
----------------------

- Initial EDI Base module: ``edi.message`` model, ``edi.connector.mixin``,
  provider-Selection field, partner GLN integration, security groups,
  views, and the abstract dispatch contract that all provider
  connectors implement.
