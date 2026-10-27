---
title: Fio banka API — Shared Client and Formats
summary: The Fio banka REST client, statement parsers and payment-order XML shared by every Fio module.
verified: 19.0.1.2.1
family: account_fio#api
---

Implements the Fio API once for all Fio modules: the REST calls with every documented error turned into a clear message, the Fio XML and JSON statement formats, the payment-order XML (`importIB.xsd`) with its domestic, SEPA and foreign orders, the reading of the bank's answer to an upload, and the Czech National Bank's list of payment reasons (*platební titul*). The token is removed from every message and log line.

It has no screen and no settings. It is installed as a dependency of the Fio modules and needs the Python library `requests`.
