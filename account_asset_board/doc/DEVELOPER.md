# account_asset_board: developer notes

Not user documentation: this file is not rendered into a page.

## Security

The schedule is computed by `account.asset.get_schedule()` running as the
current user — ACLs and record rules fully apply; only assets of the active
company are reported.
