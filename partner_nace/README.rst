=================
Partner NACE code
=================

The partner's main economic activity as its NACE code, one field for every
country: ``nace_code`` on the partner (mirrored on the company), digits only
(``62101``, not ``62.10.1``). Contacts share their company's code.

The national classifications are EU NACE plus national digits, and a partner has
one country, so the country says which variant the code is in:

* **Czech Republic:** CZ-NACE 2025 (NACE Rev. 2.1 plus a fifth digit). Since
  1. 1. 2026 every filing uses it, even one for an earlier period.
* **Slovakia:** the register (RPO) publishes NACE Rev. 2.1 classes (four digits)
  from 1. 1. 2026. The five-digit SK NACE Rev. 2 stays valid in parallel until
  the national switch in 2028.

Where it comes from and where it goes:

* ``partner_autocomplete_ares_cz`` fills it from ARES's statistical register
  (``czNacePrevazujici``, the prevailing activity);
* ``partner_autocomplete_orsf_sk`` maps the register's NACE onto it;
* the DPHDP3 (``c_okec``) and DPPDP9 (``c_nace``) returns and the Slovak Úč POD
  (``skNace``) file the company's code.

Only the code is kept. For a readable, hierarchical industry, see
``l10n_eu_nace_cssk`` on top of OCA's ``l10n_eu_nace``.
