{
    "name": "CZ Supplier Reliability — ADIS provider",
    "summary": "Czech provider for the CZ/SK supplier-reliability check: "
               "nespolehlivý plátce + zveřejněné účty from the MFČR ADIS web "
               "service (rozhraniCRPDPH).",
    "description": """
CZ Supplier Reliability provider
================================

Implements the country provider for ``l10n_cssk_payment_reliability`` against the
Czech Financial Administration ADIS SOAP web service:

* endpoint ``adisrws.mfcr.cz/.../rozhraniCRPDPH.rozhraniCRPDPHSOAP``,
  operation ``getStatusNespolehlivyPlatce`` (per the published WSDL).
* **Tax reliability** — ``nespolehlivyPlatce`` ANO → unreliable, NE → reliable,
  NENALEZEN → unknown.
* **Registered bank accounts** — the ``zveřejněné účty``: ``standardníÚčet``
  (předčíslí/číslo/kódBanky) is converted to its IBAN so it matches the bank
  account on the bill; ``nestandardníÚčet`` (already IBAN) is taken as-is.

No API key needed (the service is open).
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.0.2",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": ["l10n_cssk_payment_reliability", "l10n_cz"],
    "installable": True,
}
