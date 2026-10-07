Changelog
=========

19.0.1.1.0 (2026-10-04)
-----------------------

* A Slovak company whose chart was loaded BEFORE this module was installed
  now gets the profiles too, on install (``post_init_hook``) and on upgrade
  (migration 19.0.1.1.0). The template only applies when the chart is loaded,
  so such a company used to get none. Only missing profiles are loaded, so an
  edited useful life is never reverted; a company missing an account the
  template names is skipped with a warning rather than failing the upgrade.

19.0.1.0.0 (2026-09-21)
-----------------------

* First version: ten starter asset profiles for the Slovak chart, shipped
  through the chart template, with no default tax class and no profile for land
  or art.
