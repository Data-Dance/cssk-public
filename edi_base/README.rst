==========
EDI Base
==========

.. |badge1| image:: https://img.shields.io/badge/maturity-Production%2FStable-green.png
    :alt: Production/Stable
.. |badge2| image:: https://img.shields.io/badge/licence-Other%20proprietary-lightgray.png
    :alt: License: Other proprietary
.. |badge3| image:: https://img.shields.io/badge/Odoo-19.0-714B67.png
    :target: https://www.odoo.com
    :alt: Odoo 19.0

|badge1| |badge2| |badge3|

**EDI Base** is the shared foundation for every Data Dance EDI
integration (``edi_editel_*``, ``edi_grit_*``, …). It does **not**
implement any concrete protocol on its own — instead it provides:

* The central audit-trail model ``edi.message``, which stores every
  inbound / outbound EDI document for every provider. Inherits
  ``mail.thread`` and ``mail.activity.mixin`` so messages support
  chatter and scheduled activities for follow-up work.
* The abstract transport interface ``edi.connector.mixin`` that
  provider modules implement.
* A **multi-provider-aware cron entry point** (``_get_messages``)
  that iterates every registered provider's connector. Per-message
  processing runs under savepoints with a stub-first pattern, so a
  failure on one inbound document leaves an ``edi.message`` row
  with ``state=error`` and the raw XML attached rather than poisoning
  the whole batch.
* A **strict default policy for unresolved products** in inbound
  ORDERS via the overridable ``_edi_handle_unresolved_products(unresolved)``
  hook. Returns ``False`` by default — the import aborts with
  ``state=error``, the full payload (EAN / qty / unit / price /
  supplier code / buyer code / article name) is preserved in
  ``error_message``, and a To-Do activity is scheduled on the
  message. Add-on modules such as ``edi_base_sale_pending`` override
  to ``True`` to enable partial-handling.
* Shared, provider-agnostic helpers for turning parsed inbound
  documents into Odoo records (vendor bills from INVOIC, PO updates
  from ORDRSP, receipt updates from DESADV).
* Two access groups (``EDI / User``, ``EDI / Manager``) and the
  top-level **EDI** menu with the messages list, search and form
  views.
* GLN-driven partner resolution (sender / receiver) backed by the
  ``account_add_gln`` module's ``global_location_number``.

Installing ``edi_base`` alone is harmless — no provider is wired up
and no cron will move messages.

**Table of contents**

.. contents::
   :local:

Installation
============

Dependencies:

* ``account``
* ``account_add_gln``
* ``stock``
* ``uom_unece``

Configuration
=============

#. Make sure your company's ``global_location_number`` is set on
   ``res.company.partner_id``. Outbound messages refuse to send
   without it.
#. Optionally set a per-warehouse override ``edi_gln`` on
   ``stock.warehouse``. Outbound documents that need a Delivery Place
   (DP) GLN — DESADV, ORDERS — read it from the warehouse first and
   fall back to the company GLN.
#. For each EDI trading partner, set their
   ``global_location_number`` on ``res.partner``. Inbound messages
   are auto-linked to the partner whose GLN matches the envelope.
#. Per-partner you can choose the **EDI product code priority**
   (``product_edi_code_priority``) which controls how a partner's
   article codes are resolved to Odoo products
   (default: ``barcode`` → supplier code → internal reference).

Usage
=====

End users
~~~~~~~~~

Open **EDI → Messages** to see every transaction the system has
processed. Columns highlight test/production mode, errors and
blocking levels at a glance. Form view exposes the raw XML payload
(stored inline for < 1 MB, otherwise as ``ir.attachment``), the
correlation identifiers (``transmission_uuid``,
``provider_interchange_id``, ``external_id``) and provider-specific
links (``purchase_order_id``, ``sale_order_id``, ``picking_id``,
``vendor_bill_id``, …) added by downstream modules.

Manual operations
~~~~~~~~~~~~~~~~~

* **Reprocess** — re-run inbound dispatch (state → ``received``).
* **Retry Send** — re-queue a failed outbound (state → ``ready``).
* **Chatter** on the message form for free-form notes and follower
  subscriptions.
* **Activities** scheduled on the message (e.g. To-Do raised by the
  strict-mode failure path) appear in the standard activity views.

Developers
~~~~~~~~~~

* Implement a new provider by inheriting ``edi.connector.mixin`` and
  overriding ``_authenticate()``, ``_send_message()``,
  ``_poll_inbound()`` and ``_acknowledge_inbound()``.
* Register the provider on ``edi.message`` by extending
  ``PROVIDER_CONNECTOR_MAP``, ``PROVIDER_CRON_MAP``,
  ``_selection_provider()`` and ``_default_provider()``.
* Reuse the pivot-format helpers exposed on ``edi.message``:

  * ``_create_vendor_bill_from_parsed(vendor, parsed)``
  * ``_update_po_lines_from_parsed(order, parsed_items)``
  * ``_update_picking_from_parsed(picking, parsed_articles)``

* Inject your country-specific or partner-specific behaviour via the
  no-op hooks ``_hook_post_create_vendor_bill``,
  ``_hook_post_update_po_lines``, ``_hook_post_update_picking``,
  ``_hook_post_create_sale_order``, ``_hook_validate_outbound_xml``.
* Override ``_edi_handle_unresolved_products(unresolved)`` to switch
  the inbound ORDERS policy from strict (raise on missing product) to
  partial. See ``edi_base_sale_pending`` for a reference
  implementation that persists unresolved lines as
  ``edi.pending.line`` records.
* Override ``_edi_unresolved_activity_user_id()`` to route the
  recovery To-Do to a specific user instead of the env user.

Models & fields
===============

``edi.message`` (new, ``mail.thread`` + ``mail.activity.mixin``)
    Single audit-log model. Key fields: ``provider``, ``direction``,
    ``state``, ``message_type``, ``doc_type_code`` (more reliable than
    ``message_type``), ``message_id`` (unique with direction),
    ``sender_gln`` / ``receiver_gln`` (auto-resolve to
    ``partner_id``), ``message_xml`` (inline) or ``attachment_id``
    (large payloads), ``transmission_uuid``,
    ``provider_interchange_id``, ``external_id``,
    ``blocking_level``, ``error_message``.
    Hooks: ``_edi_handle_unresolved_products(unresolved)`` (default
    strict — returns ``False``), ``_format_unresolved_products_error``
    (renders human-readable error_message),
    ``_edi_unresolved_activity_user_id`` (recovery To-Do assignee).

``edi.connector.mixin`` (abstract)
    Transport contract — four stub methods that providers override.

``res.partner`` (extended)
    Adds ``product_edi_code_priority`` (Selection).

``stock.warehouse`` (extended)
    Adds ``edi_gln`` (Char) — Delivery Place GLN override.

``res.config.settings`` (extended)
    Anchor for provider-specific configuration sections.

Security
========

* **EDI / User** (``group_edi_user``) — read-only on
  ``edi.message``; sees the EDI menu.
* **EDI / Manager** (``group_edi_manager``) — full read/write/create
  on ``edi.message`` (no delete — audit trail).

Known issues / Roadmap
======================

* No native COMDIS / control-message handling yet — provider modules
  add their own where required.
* Message search performance relies on the indexes on
  ``transmission_uuid``, ``provider_interchange_id``, ``external_id``,
  and ``message_id`` — adding very large XML payloads inline (rather
  than as attachments) can slow the form view.

Bug Tracker
===========

Bugs are reported privately to Data Dance s.r.o. via
support@datadance.eu.

Credits
=======

Authors
~~~~~~~

* Data Dance s.r.o.

Maintainers
~~~~~~~~~~~

* `Data Dance s.r.o. <https://www.datadance.eu>`_

License
~~~~~~~

Data Dance Proprietary License v1.0 — see ``LICENSE`` and ``__manifest__.py``.
