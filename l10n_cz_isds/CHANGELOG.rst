=========
Changelog
=========

All notable changes to **l10n_cz_isds** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[19.0.1.1.0] — 2026-11-10
-------------------------

Added
~~~~~

- Signing in with a certificate: a system certificate registered on the box
  for an external application (no password), or a login and password
  together with a certificate. The certificate's key is loaded into the TLS
  context from a file encrypted with a one-time password and deleted before
  the connection is made.

Changed
~~~~~~~

- Redirects are no longer followed, so neither the login nor the
  certificate can be carried to another host.

[19.0.1.0.0] — 2026-11-10
-------------------------

Added
~~~~~

- The company's data box: environment (test or production), the login of a
  data box user, and **Test Connection**, which shows whose box it opens.
- A client for the operator's web services (WSDL/XSD 3.11): sending a data
  message with attachments, listing received messages, downloading one. Every
  request is validated against the operator's schema in the tests.
