=========
Changelog
=========

All notable changes to **currency_rate_sk_base** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.0.1] — 2026-07-04
-------------------------

Added
~~~~~

- Shared, edition-agnostic Slovak commercial-bank FX feed helpers exposed as pure
  functions under ``odoo.addons.currency_rate_sk_base.utils.sk_rates`` (no models).
- ``parse_vub`` — parses the VÚB banka *kurzový lístok* text feed (Devíza stred /
  middle rate); ``parse_tb`` — parses the Tatra banka exchange-rate RSS feed.
- ``fetch_vub_text`` / ``fetch_tb_text`` HTTP fetchers plus the per-bank
  supported-currency lists.
- Rates are expressed as ``1 EUR = X`` foreign currency; parse functions return
  ``{date: {ccy: rate_str}}`` so the CE (OCA ``res.currency.rate.provider``) and EE
  (``currency_rate_live``) SK providers reuse the feed logic without duplication.
