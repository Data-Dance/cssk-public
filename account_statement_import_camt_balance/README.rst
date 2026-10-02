===================================================
CAMT import: statements that pass the balance check
===================================================

Two ways a correct CAMT.053 fails the balance check with OCA's
``account_statement_import_camt``, both found on real Tatra banka statements:

**A closing balance per day.** A monthly statement may carry one ``CLBD`` for
every day with movements (24 in one April file). The OCA parser takes the first
one, so the statement closes on the first day's balance. This module takes the
**latest** ``CLBD`` and the earliest ``OPBD`` / ``PRCD``, by date, or by document
order where the balances have no date.

**One transaction in several detail blocks.** The parser makes one line per
``TxDtls``, and a block without its own ``Amt`` / ``TxAmt`` inherits the whole
entry amount. Tatra banka writes a fee as one block with the references and one
with the amount in ``InstdAmt``, so the fee is booked twice. When the lines of
an entry do not add up to the entry, its blocks are merged into one line. A
genuine batch, whose blocks carry their own amounts and add up, is left as it is.

Both are candidates for a pull request to OCA ``bank-statement-import``. This
module is the stopgap until one is merged.
