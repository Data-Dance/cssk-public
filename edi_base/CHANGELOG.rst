=========
Changelog
=========

All notable changes to **edi_base** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[19.0.1.8.0] — 2026-09-29
-------------------------

Changed
~~~~~~~

- **A message belongs to its company, and is sent and processed as it.** A new
  message without a company takes the company of the document it links to (not
  the user's current company). Outbound sends run with the connector in the
  message's company, and inbound processing and reprocessing run in the
  message's company, which a provider may have routed away from the polling
  company. So a connector can take credentials and the sender's identity from
  ``env.company`` in a database with several companies.
- An inbound stub a provider parks (state ``error`` at creation, e.g. a
  receiver it cannot route) is stored and acknowledged but not processed.

[19.0.1.7.1] — 2026-09-28
-------------------------

Fixed
~~~~~

- **EDI orders failed with** ``'res.partner' object has no attribute
  'product_edi_code_priority'``. 1.7.0 removed the field on the premise that
  nothing read it; ``_resolve_product`` did, on every inbound line. The
  lookup order is now fixed at the one every partner carried — the field's
  default, ``barcode__supplier_code__default_code``: barcode, then the
  sender's ``product.supplierinfo`` code, then ``default_code``. The 1.7.0
  note below that "no module in the family ever read it" was wrong; the
  column is gone either way, so there is nothing to migrate.

[19.0.1.7.0] — 2026-09-24
-------------------------

Changed
~~~~~~~

- **The inbound document creators left this module.**
  ``_create_vendor_bill_from_parsed``, ``_update_po_lines_from_parsed``,
  ``_create_standalone_picking`` and ``_update_picking_from_parsed`` — with
  the no-op hooks ``_hook_post_create_vendor_bill``,
  ``_hook_post_update_po_lines`` and ``_hook_post_update_picking`` — are now
  in ``edi_base_purchase``, where their only callers already were. The block
  was already referencing ``edi_base_purchase.activity_desadv_unmatched``,
  so it had assumed that layering for some time.
  ``_hook_post_create_sale_order`` moved to ``edi_base_sale``. Product
  resolution stays here: the purchase-side creators call it as well, and
  ``product`` arrives with ``account``.
- **The GS1 party layer left this module** for the new ``edi_base_gs1``:
  ``res.partner.edi_communication_partner_id``,
  ``res.partner.edi_desadv_sscc_mode``, ``stock.warehouse.edi_gln``,
  ``_edi_envelope_partner()`` and ``_edi_use_sscc_desadv()``.
- **Dropped the ``stock`` and ``uom_unece`` dependencies.** Both were used
  only by what moved. A Peppol-only install no longer pulls in the Inventory
  app, and the ePošťák chain now depends on nothing outside Odoo core.

Removed
~~~~~~~

- ``res.partner.product_edi_code_priority``. No module in the family ever
  read it. Odoo removes the ``ir.model.fields`` row and **drops the column**
  — verified on a test upgrade, where an earlier note here claiming the
  column survives turned out to be wrong. Nothing read the values, so
  nothing is lost, but this is what proves the hand-over below is not
  ceremonial: the same cleanup would have taken the three moved columns.

Migration
~~~~~~~~~

- ``migrations/19.0.1.7.0/pre-migrate.py`` hands the three moved field
  definitions to ``edi_base_gs1`` and schedules that module for install
  where ``edi_editel_base``, ``edi_grit_base`` or ``edi_base_purchase`` is
  present. **Upgrade with ``-u edi_base`` (or ``-u all``).**
- Tested on a database mirroring a customer's installed set (one partner
  with a communication endpoint, four with SSCC mode, one warehouse GLN):
  the migration reassigns the three definitions, ``edi_base_gs1`` installs
  in the same run, and all three values survive.
- **Upgrading only a provider module fails loudly, and that is fine.**
  ``-u edi_editel_base`` alone leaves this module's view in the database
  still referencing ``product_edi_code_priority``, which the new code no
  longer defines, so view validation raises and the whole registry load is
  rolled back. Nothing is written and no data is touched — the database is
  exactly as it was, and the fix is to run the upgrade properly.

[19.0.1.6.0] — 2026-08-28
-------------------------

- **Add ``edi.message._post_dispatch_trace()``**, called from ``_enqueue_send``
  — the single funnel every outbound dispatch goes through — so the business
  document gets a chatter line when the message is actually handed to the
  queue. Until now the only chatter came from the provider's
  ``_*_emit_invoic`` at *generation* time, so a document generated with
  auto-send off and dispatched later from the EDI message form left no trace
  on the invoice at all: the send was visible only on ``edi.message`` and
  ``queue.job``. ORDRSP and DESADV emit paths posted nothing whatsoever.

  *Found in production*: after regenerating an INVOIC, an invoice carried two
  "INVOIC sent via Editel EDI" chatter lines 90 seconds apart, for a document
  that had gone out exactly once. Reading the chatter, it was indistinguishable
  from a double send; only ``queue.job`` showed the truth.

- **Add ``edi.message._edi_related_documents()``** — the hook
  ``_post_dispatch_trace`` resolves its targets through. ``edi_base`` owns no
  document links (they live in ``edi_base_sale`` / ``edi_base_purchase``), so
  the default returns an empty list and each satellite appends its own anchor.

  Nothing in ``_post_dispatch_trace`` may raise: ``with_delay()`` has already
  created the ``queue.job`` row in the same transaction, so an escaping
  exception rolls the dispatch back and the document is silently never sent.
  The ``_edi_related_documents()`` call is therefore *inside* the guard, not
  outside it, and posts are deduplicated by ``(model, id)``.

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
