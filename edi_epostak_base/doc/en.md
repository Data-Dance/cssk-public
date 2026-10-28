---
title: ePošťák — Base
summary: Registers ePošťák as an EDI provider, holds the sandbox / production switch and the firm ID, and checks the Peppol addresses every ePošťák call is made with.
verified: 19.0.1.1.0
family: edi_epostak_peppol#setup
---

Registers the **ePošťák** provider on EDI messages, adds the **ePošťák Environment** switch (Sandbox / Production, for the whole database) and each company's **ePošťák Firm ID** to *Settings → EDI*, polls each company's inbox as that company, stamps the environment on every message when it is created, and sends ePošťák messages by scheduled action, without a job runner. It reads the Peppol routing data from the document itself and refuses, with a readable message, a company whose Peppol address is missing or uses scheme 0245 with anything but a ten-digit DIČ. It also adds the scheduled action *ePošťák: Poll Inbound Documents*.

It is installed with [module:edi_epostak_peppol](module:edi_epostak_peppol); on its own it connects nowhere — the connection is [module:edi_epostak_connector_sapi](module:edi_epostak_connector_sapi).
