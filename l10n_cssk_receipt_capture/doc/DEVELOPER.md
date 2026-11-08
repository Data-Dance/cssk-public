# l10n_cssk_receipt_capture: developer notes

Not user documentation: this file is not rendered into a page.

## Provider behaviour

**The VAT recap is a model, not two fields.** A receipt's own per-rate summary
is the only trustworthy figure, and it does not fit in a pair. A Slovak
restaurant bill routinely carries three rates — food 5 %, non-alcoholic drinks
19 %, alcohol 23 % — and the legacy two-slot "basic / reduced" recap that tax
authorities still emit cannot express that. Worse, it is unreliable: measured on
two real receipts, it carried **stale 20/10 rate labels** on one (while the items
and the real recap said 23/5) and arrived **entirely null** on the other.
