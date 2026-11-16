=========
Changelog
=========

18.0.1.0.2 (2026-11-16)
=======================

* **Fixed: a chart reload put every salary rule back on the default accounts** (cssk-public#47). Each load of the Slovak chart wrote the default debit/credit pair on every mapped rule, so separate social and health insurer accounts (for example 336100 / 336250) went back to 336000. A company's usable pair, including an intentionally empty opposite side, is now kept; a side holding another company's account, or a pair cleared on both sides, gets the default, resolved within the company's own accounts. Port of 19.0.1.0.5.

18.0.1.0.1 (2026-07-06)
=======================

* i18n pass: added ``i18n/<module>.pot`` and ``i18n/sk.po`` (module exposes no localizable source strings beyond inherited framework labels; Slovak GL account names remain in code comments only).

