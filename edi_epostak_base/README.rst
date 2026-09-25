==================
ePošťák EDI Base
==================

Base module for **ePošťák** (https://epostak.sk), a Slovak **Peppol Access
Point**. It registers the ``epostak`` provider on ``edi.message``, owns the
sandbox/production switch, and derives the Peppol addressing metadata that any
ePošťák wire protocol needs.

The concrete transport lives in ``edi_epostak_connector_sapi``; the bridge to
the document standard lives in ``edi_epostak_peppol``. This split mirrors the
Editel and GRiT provider stacks.

Why the metadata is read out of the UBL
=======================================

ePošťák wants routing metadata (sender/receiver participant, document type id,
process id) *alongside* the document, and rejects a submission whose metadata
disagrees with the ``cbc:EndpointID`` inside the payload (error
``SAPI-DOC-025``). So the document is treated as the single source of truth:
``_epostak_parse_ubl`` reads the participants from the UBL's own EndpointID
elements — ``schemeID`` attribute included — and composes the Peppol document
type identifier structurally::

    <root-namespace>::<root-element>##<CustomizationID>::<UBLVersionID>

which yields the right identifier for a BIS3 Invoice, a CreditNote and an
ApplicationResponse alike, with no per-document-kind table to keep in sync.

Both UBL party shapes are handled: ``cac:AccountingSupplierParty`` /
``cac:AccountingCustomerParty`` on an invoice, and ``cac:SenderParty`` /
``cac:ReceiverParty`` on an ApplicationResponse — so an Invoice Response we
send as the *buyer* is addressed correctly too.

Configuration
=============

#. Install a transport connector (``edi_epostak_connector_sapi``).
#. In *Settings ▸ EDI ▸ ePošťák* pick the environment (Sandbox / Production).
#. On the company partner set **Peppol e-address (EAS)** and **Peppol
   Endpoint** — every ePošťák request is scoped to that participant. For a
   Slovak company this is EAS ``0245`` (SK DIČ) with the DIČ value.
#. Only for integrator keys (``sk_int_*``), which speak for several firms: set
   the **ePošťák Firm ID** so requests carry ``X-Firm-Id``.
