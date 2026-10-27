---
title: ePošťák — Connector (SAPI-SK 1.0)
summary: The connection to the ePošťák access point — credentials, sending, collecting received documents, delivery status and the Peppol reachability check.
verified: 19.0.1.1.2
family: edi_epostak_peppol#statuses
---

Talks to ePošťák over its SAPI-SK 1.0 interface: logs in with the **Client ID** and **Client Secret** of the active environment, sends each Peppol document (*Sent* means accepted for transport, not delivered), collects documents waiting for your Peppol address and acknowledges them only after they are stored, and every 30 minutes asks ePošťák whether sent documents were delivered (*Done*) or failed (*Error*). It adds **Test Connection**, the **Last inbound poll** line with **Poll inbound now**, a To-Do after repeated failed collections, the *Transfer Tuning* settings and **Check Peppol reachability** on contacts.

Install it together with [module:edi_epostak_peppol](module:edi_epostak_peppol); the whole setup is described in [the ePošťák guide](module:edi_epostak_peppol#setup).
