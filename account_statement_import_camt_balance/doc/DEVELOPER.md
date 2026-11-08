# account_statement_import_camt_balance: developer notes

Not user documentation: this file is not rendered into a page.

## Parser behaviour

**One transaction in several detail blocks.** The parser makes one line per
`TxDtls`, and a block without its own `Amt` / `TxAmt` inherits the whole
entry amount. Tatra banka writes a fee as one block with the references and one
with the amount in `InstdAmt`, so the fee is booked twice. When the lines of
an entry do not add up to the entry, its blocks are merged into one line. A
genuine batch, whose blocks carry their own amounts and add up, is left as it is.
