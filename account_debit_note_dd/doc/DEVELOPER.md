# account_debit_note_dd: developer notes

Not user documentation: this file is not rendered into a page.

## How a debit note is recognised

- The printed invoice document is titled **Debit Note** (draft / cancelled
  variants included) whenever a posted customer invoice carries a
  `debit_origin_id`.
* The standard **Reverse** button is hidden on the invoice form (debit notes are
  created through the dedicated debit-note flow, not via reversal).
* The customer *Credit Notes* action is widened to also list customer invoices
  that have a `debit_origin_id`, so customer debit notes are reachable from
  the same place. Vendor debit notes are not listed.
