=========
Changelog
=========

Unreleased
----------

* Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

19.0.1.1.1 (2026-09-07)
-----------------------

* **An accountant could not actually remit.** The ACL granted
  ``account.group_account_user`` the wizard and nothing else, while the flow
  searches ``hr.wage.garnishment.line`` and writes ``state``/``move_id`` on it
  — so an accountant with no HR role hit ``AccessError`` on this module's
  headline workflow. Symmetrically, the *Remit to Payee* list button carried no
  ``groups``, so an HR-only user reaching it failed on ``account.move.create``.
  The ACL now grants what remitting needs and the button is gated to the group
  that can complete it.
* Remitting stays confined to what it is for: a ``write`` guard limits a
  non-payroll user to ``state`` and ``move_id``, so the new ACL cannot become a
  way for anyone who can post an entry to change how much is withheld from an
  employee's wage. The chatter note on the order is posted by the system rather
  than by widening the accountant's rights on the order itself.
* **The order's own payee bank account never reached the entry.** The order
  carries one precisely because a bailiff collects for several cases on
  different accounts; dropped here, ``account_payment_order`` downstream fell
  back to the payee's default account, and for an exekútor money on the wrong
  account is not credited to the case.

19.0.1.0.0 (2026-07-27)
-----------------------

* Initial release.
