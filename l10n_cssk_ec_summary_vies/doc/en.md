---
title: CZ/SK EC Sales List — VIES Check
summary: Checks every EC sales list line against VIES at export and keeps the VIES consultation number on the line as proof.
verified: 19.0.1.0.4
family: l10n_cssk_ec_summary_base#vies
---

Makes the EC sales list export ask the European Commission's VIES service whether each customer VAT number is valid, and stores the result, the consultation number and the time of the check on the line. An invalid number blocks the export without losing the proofs already obtained; a VIES outage does not block it and is noted in the chatter.

It installs itself when both the EC sales list framework and the direct VIES module (`l10n_cssk_vies`) are installed, and acts only for companies with **Use direct EU VIES (no IAP)** switched on.
