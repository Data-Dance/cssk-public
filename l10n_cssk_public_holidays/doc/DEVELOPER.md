# l10n_cssk_public_holidays: developer notes

Not user documentation: this file is not rendered into a page.

## Maintenance

Edit the rule tables in `models/calendar_public_holiday.py` (`SK_FIXED`,
`CZ_FIXED` and the Easter offsets). Each fixed rule carries a first year, a
last year and a set of skipped years. Add a test for the new year.
Lines already generated for a year the change affects are not removed, so
delete that year's record and regenerate it.
