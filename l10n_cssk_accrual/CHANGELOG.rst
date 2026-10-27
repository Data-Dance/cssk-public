=========
Changelog
=========

All notable changes to **l10n_cssk_accrual** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.1.0] — 2026-10-27
-------------------------

Fixed
~~~~~

- **A cancelled estimate that had been posted can be reset to draft.**
  Cancelling reverses the entry rather than unposting it, so *Reset to
  Draft* — offered on every cancelled estimate — always refused. The
  estimate now lets go of the cancelled entry and its reversal, which stay
  in the books and are named in the chatter; posting again books a new
  entry. *Reset to Draft* now refuses anything but a cancelled estimate.

Changed
~~~~~~~

- The accrual types are *Estimated payable* and *Estimated receivable*,
  without account numbers: the receivable named 388, which the Slovak chart
  does not have (an unbilled receivable goes on a separate analytic account
  of the receivable, § 48 ods. 3 opatrenia 740/2002). The help of *Accrual
  Account* names the accounts of both countries.
- README and description: 326 is for unbilled supplies whose amount is
  **known** (§ 50 ods. 6), not a Slovak *dohadná položka*; an uncertain
  amount is a provision on 323.

[19.0.1.0.4] — 2026-09-13
-------------------------

Fixed
~~~~~

- **Code translations that Odoo was never loading.** An entry whose references
  are ``code:addons/...`` is treated as a Python translation only if it carries
  the extracted comment ``#. odoo-python`` — ``_load_python_translations``
  filters on exactly that and never on the reference. Without it an entry can
  name the right ``.py``, carry a correct msgstr, pass ``msgfmt --check``, and
  be silently ignored for ever. This module's hand-added entries were in that
  state. Repaired by ``tools/fix_po_code_comments.py``, which is also the CI
  check; the offline exporter now emits the comment itself.

[19.0.1.0.3] — 2026-09-13
-------------------------

Fixed
~~~~~

- **Terms the translation catalogue never carried.** Strings that reach the
  user were absent from the template — a field with no ``string=``, a mixin
  field addressed to the abstract model's ``ir.model.fields`` row rather
  than each concrete one, or a whole category the offline exporter never
  emitted. An absent term cannot be translated and shows English in an
  otherwise Slovak or Czech screen. The template and the catalogues now carry them,
  and the Slovak or Czech is written.

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.0.2] — 2026-07-04
-------------------------

Added
~~~~~

- CZ/SK **estimated accruals** (dohadné položky) — items where the obligation
  exists but the exact amount is not yet known (distinct from časové rozlíšenie
  deferrals, and shipped by neither Odoo CE nor EE).
- ``cssk.accrual.estimate`` with the **link & true-up** workflow: book an estimate
  at period end (estimated payable Dr expense / Cr accrual — CZ 389, SK 326;
  estimated receivable Dr accrual CZ 388 / Cr income), then link the actual
  invoice — the estimate is reversed at the invoice date and reconciled against
  the accrual account, so only the difference remains and the accrual clears.
- Accounts and journal chosen per estimate (no hard-coded chart), so it works for
  the Czech, Slovak and any custom chart.
- CE-clean (Odoo core ``account`` + ``l10n_cssk_core``).

[2026-06-30] — i18n sweep & baseline
------------------------------------

Added
~~~~~

- Full cs_CZ + sk_SK translations (Odoo 19 jsonb).
