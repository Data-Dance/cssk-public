===================
EDI Base: Peppol
===================

Provider-neutral **Peppol BIS Billing 3.0** support: generate and receive
invoices / credit notes, and handle business responses (MLR today; Invoice
Response next), over **any** EDI transport provider.

The document standard lives here; the transport does not. A provider module
(e.g. ``edi_editel_peppol`` for Editel eXite, or a future ``edi_grit_peppol``
for GRiT Orion) supplies just two hooks on ``account.move``:

* ``_peppol_provider()`` — the provider key stamped on the outbound
  ``edi.message`` (``doc_family='peppol'``);
* ``_peppol_send(msg)`` — enqueue that message via the provider's connector.

Everything else — BIS3 UBL generation (Odoo core ``account.edi.xml.ubl_bis3``),
UBL classification, inbound vendor-bill creation, the MLR handling, the "Send
via Peppol" button, the Peppol Messages tab, and the settings — is here and
shared.

This module deliberately does **not** use Odoo's ``account_peppol`` /
``account_peppol_response``, whose send/receive path is hard-wired to Odoo's
own SAS access point.

Configuration
=============

#. Install a transport provider module (e.g. ``edi_editel_peppol``) and set its
   connector credentials.
#. On your company partner set **Peppol e-address (EAS)** + **Peppol Endpoint**;
   likewise on each customer/vendor.
#. Optionally, in *Settings ▸ EDI ▸ Peppol BIS3*, enable **Auto-send Peppol on
   Invoice Post** and/or pick the **Peppol Purchase Journal** for inbound bills.
