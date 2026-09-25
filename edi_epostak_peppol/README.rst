====================
ePošťák EDI: Peppol
====================

Sends and receives **Peppol BIS Billing 3.0** invoices, credit notes and
business responses over the Peppol network using **ePošťák** as the access
point.

For the Slovak jurisdiction the mandated format is *plain* Peppol BIS 3 /
UBL 2.1 / EN 16931 — there is no national billing CIUS. Transport and document
standard stay cleanly separated:

* **Document** — produced by Odoo (``account_edi_ubl_cii``), through whichever
  BIS3 builder the customer's format resolves to. With ``l10n_sk_ubl_bis3``
  installed that is ``account.edi.xml.ubl_sk``, which additionally maps the
  *variabilný symbol* onto ``cbc:PaymentID`` (BT-83).
* **Transport** — ``edi.message`` + ``edi_epostak_connector_sapi``. The BIS3
  UBL goes on the wire as-is; routing is read from the ``cbc:EndpointID`` of
  the party blocks inside the document.

This module deliberately does **not** use Odoo's ``account_peppol``, whose
send/receive path is hard-wired to Odoo's own SAS access point.

Choosing the transport
======================

``account.move._peppol_provider()`` is single-valued, so with more than one
Peppol transport installed (ePošťák alongside ``edi_editel_peppol``, say) the
winner would be decided by module load order. Set **Peppol Transport** in
*Settings ▸ EDI ▸ Peppol BIS3* to make the choice explicit; leave it empty to
use ePošťák. Dispatch itself routes on the provider stamped on each message,
so documents already prepared under the previous transport still leave through
it.

Configuration
=============

#. Configure ``edi_epostak_connector_sapi`` (environment + credentials) and
   the company partner's Peppol EAS + endpoint.
#. On each customer/vendor set their EAS + endpoint.
#. Optionally, in *Settings ▸ EDI ▸ Peppol BIS3*, enable **Auto-send Peppol on
   Invoice Post** and/or pick the **Peppol Purchase Journal** for inbound
   bills.

Usage
=====

* **Send**: post a customer invoice/credit note, then click **Send via
  Peppol** (or enable auto-send). Track delivery on the linked ``edi.message``:
  ``sent`` means ePošťák accepted it for transport, ``done`` means the network
  confirmed delivery to the recipient's access point.
* **Receive**: the ePošťák inbound cron drains the participant mailbox; UBL
  Invoice/CreditNote payloads are imported as **draft vendor bills**, and
  ApplicationResponses (MLR / Invoice Response) are recorded against the
  document they answer.
