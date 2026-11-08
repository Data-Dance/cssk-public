# l10n_cz_epo: developer notes

Not user documentation: this file is not rendered into a page.

## Interface

Source: *Obecný popis struktury souborů a rozhraní pro třetí strany
společného technického zařízení správců daně (Podatelny EPO)*, verze 1.11,
https://adisspr.mfcr.cz/dpr/adis/idpr_pub/epo2_info/PodatelnaEPO.pdf. See
also `docs/epo-validation-research.md` in the repository.

- Checking and filing are the same call except for one parameter; the check
  passes it literally and has no path to a filing, and filing is refused
  unless explicitly allowed on the company.
* Only users in the filing group can make EPO calls, checked on the server.
* A filing whose outcome is unknown — the request may have reached EPO but
  no answer came back — is **not retried automatically**, since that could
  file the return twice. The submission fails with a message to check the
  filing in the portal first. Only a connection that was never established
  is retried. The same holds for any unexpected error, including one raised
  while recording EPO's potvrzení: the submission fails with the podací
  číslo in the message and is never sent again on its own.
* The channel is offered only for companies whose fiscal country is Czechia.
* EPO's own caveat is repeated in the interface: its checks are a subset of
  the tax office's, so a clean check is not a guarantee of acceptance.
