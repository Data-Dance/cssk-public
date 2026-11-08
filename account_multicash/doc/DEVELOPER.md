# account_multicash: developer notes

Not user documentation: this file is not rendered into a page.

## Rendering

The file rendering is delegated to `account_cz_bankfile_base`; this addon only
feeds it the normalized payment items from the payment lines and resolves the
target format from the payment method.
