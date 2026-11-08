# account_abo: developer notes

Not user documentation: this file is not rendered into a page.

## Rendering

The module exports domestic credit transfers (úhrady, ABO data type 1501). The
actual file rendering is delegated to `account_cz_bankfile_base`; this addon
only feeds it the normalized payment items from the payment lines.
