# edi_base: developer notes

Not user documentation: this file is not rendered into a page.

## Developers

* Implement a new provider by inheriting `edi.connector.mixin` and
  overriding `_authenticate()`, `_send_message()`,
  `_poll_inbound()` and `_acknowledge_inbound()`.
* Register the provider on `edi.message` by extending
  `PROVIDER_CONNECTOR_MAP`, `PROVIDER_CRON_MAP`,
  `_selection_provider()` and `_default_provider()`.
* Reuse the pivot-format helpers exposed on `edi.message`:

  * `_create_vendor_bill_from_parsed(vendor, parsed)`
  * `_update_po_lines_from_parsed(order, parsed_items)`
  * `_update_picking_from_parsed(picking, parsed_articles)`

* Inject your country-specific or partner-specific behaviour via the
  no-op hooks `_hook_post_create_vendor_bill`,
  `_hook_post_update_po_lines`, `_hook_post_update_picking`,
  `_hook_post_create_sale_order`, `_hook_validate_outbound_xml`.
* Override `_edi_handle_unresolved_products(unresolved)` to switch
  the inbound ORDERS policy from strict (raise on missing product) to
  partial. See `edi_base_sale_pending` for a reference
  implementation that persists unresolved lines as
  `edi.pending.line` records.
* Override `_edi_unresolved_activity_user_id()` to route the
  recovery To-Do to a specific user instead of the env user.

## Models & fields

`edi.message` (new, `mail.thread` + `mail.activity.mixin`)
    Single audit-log model. Key fields: `provider`, `direction`,
    `state`, `message_type`, `doc_type_code` (more reliable than
    `message_type`), `message_id` (unique with direction),
    `sender_gln` / `receiver_gln` (auto-resolve to
    `partner_id`), `message_xml` (inline) or `attachment_id`
    (large payloads), `transmission_uuid`,
    `provider_interchange_id`, `external_id`,
    `blocking_level`, `error_message`.
    Hooks: `_edi_handle_unresolved_products(unresolved)` (default
    strict — returns `False`), `_format_unresolved_products_error`
    (renders human-readable error_message),
    `_edi_unresolved_activity_user_id` (recovery To-Do assignee).

`edi.connector.mixin` (abstract)
    Transport contract — four stub methods that providers override.

`res.partner` (extended)
    EDI fields (GLN, auto-send override); see `edi_base_gs1` for the
    communication endpoint and SSCC mode.

`stock.warehouse` (extended)
    Adds `edi_gln` (Char) — Delivery Place GLN override.

`res.config.settings` (extended)
    Anchor for provider-specific configuration sections.

## Known issues / Roadmap

* No native COMDIS / control-message handling yet — provider modules
  add their own where required.
* Message search performance relies on the indexes on
  `transmission_uuid`, `provider_interchange_id`, `external_id`,
  and `message_id` — adding very large XML payloads inline (rather
  than as attachments) can slow the form view.
