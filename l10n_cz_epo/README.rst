============================================================
CZ EPO: check and file through Finanční správa
============================================================

Sends Czech statutory filings — přiznání k DPH (DPHDP3), kontrolní hlášení
(DPHKH1), souhrnné hlášení, OSS and the other statements on the submission
pipeline of ``l10n_cssk_submission_base`` — to **EPO** (*Elektronická podání
pro Finanční správu*) through its published interface for third-party
software, signed with the company's qualified certificate.

What EPO is
===========

EPO is the Czech tax administration's electronic filing gateway, behind the
MOJE daně portal. A filing reaches it in one of three ways: filled in or
uploaded in the web form, sent from the company's data box (datová
schránka), or — what this module does — posted directly by accounting
software to the **Podatelna EPO** interface.

That interface has **no accounts and no API keys**. A filing is the XML
wrapped in a PKCS#7 signed object, signed with a **qualified electronic
signature** (ZAREP) issued by I.CA, PostSignum or eIdentity; the signature is
the identity. Its test mode (``?test=1``) runs every check — the signature,
the structure, the content — and files nothing, returning a list of errors.
A real filing returns a signed **potvrzení** with the **podací číslo**; the
state of processing (accepted / rejected) is then asked for separately.
EPO never returns a PDF.

Source: *Obecný popis struktury souborů a rozhraní pro třetí strany
společného technického zařízení správců daně (Podatelny EPO)*, verze 1.11,
https://adisspr.mfcr.cz/dpr/adis/idpr_pub/epo2_info/PodatelnaEPO.pdf. See
also ``docs/epo-validation-research.md`` in the repository.

What this module does
=====================

* **EPO certificates** (Accounting → Configuration → EPO certificates): the
  company's qualified certificate with its private key, as a ``.p12`` /
  ``.pfx`` file and its password. Readable and changeable only by the group
  allowed to file (*Statutory submissions: file*). The file must include the
  intermediate certificates of the issuer's chain.
* A submission channel **EPO — Finanční správa (signed, direct)**:

  * **Check with EPO** signs the filing and sends it in test mode. EPO's
    answer is stored on the submission (No errors / Warnings only / Errors,
    the list, and the XML). It never files and never changes the
    submission's state.
  * **Queue / Send** files for real — only if the company has switched on
    **Allow filing through EPO** (company form, page *EPO podání*). Off by
    default: a company can check through EPO without being able to file.
    The signed payload and EPO's potvrzení are kept on the submission, and
    the podací číslo becomes its authority reference.
  * The scheduled poll asks EPO for the state until the tax office has
    accepted or rejected the filing. A large filing that EPO processes
    off-line is followed to its potvrzení first.

Safety
======

* Checking and filing are the same call except for one parameter; the check
  passes it literally and has no path to a filing, and filing is refused
  unless explicitly allowed on the company.
* Only users in the filing group can make EPO calls, checked on the server.
* A filing whose outcome is unknown — the request may have reached EPO but
  no answer came back — is **not retried automatically**, since that could
  file the return twice. The submission fails with a message to check the
  filing in the portal first. Only a connection that was never established
  is retried.
* EPO's own caveat is repeated in the interface: its checks are a subset of
  the tax office's, so a clean check is not a guarantee of acceptance.

Known limits
============

* The response format of the live service is implemented from the
  specification and has not been confirmed against it from this code base.
* The corporate income tax return (DPPDP9) is not on the submission pipeline
  yet, so it cannot be sent through this channel.
* Subscribe to Finanční správa's vendor list (``epodpora@fs.gov.cz``, subject
  "Přihlášení k zasílání informací o EPO") for interface changes.

Credits
=======

* Data Dance s.r.o.
