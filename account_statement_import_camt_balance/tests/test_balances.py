# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase, tagged

BALANCE = """
            <Bal>
                <Tp><CdOrPrtry><Cd>{code}</Cd></CdOrPrtry></Tp>
                <Amt Ccy="EUR">{amount}</Amt>
                <CdtDbtInd>CRDT</CdtDbtInd>
                {date}
            </Bal>"""

STATEMENT = """<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.053.001.02">
    <BkToCstmrStmt>
        <GrpHdr><MsgId>DAILY-1</MsgId><CreDtTm>2026-05-01T08:00:00</CreDtTm></GrpHdr>
        <Stmt>
            <Id>DAILY-1/2026-04</Id>
            <CreDtTm>2026-05-01T08:00:00</CreDtTm>
            <Acct><Id><IBAN>SK2411000000002925916220</IBAN></Id><Ccy>EUR</Ccy></Acct>
            {balances}
            {entries}
        </Stmt>
    </BkToCstmrStmt>
</Document>
"""


SIMPLE_ENTRY = """
            <Ntry>
                <Amt Ccy="EUR">100.00</Amt>
                <CdtDbtInd>CRDT</CdtDbtInd>
                <Sts>BOOK</Sts>
                <BookgDt><Dt>2026-04-01</Dt></BookgDt>
                <ValDt><Dt>2026-04-01</Dt></ValDt>
            </Ntry>"""

# Tatra banka: one 7.00 fee, told in two NtryDtls blocks; only the second has
# an amount, and in InstdAmt, which the OCA parser does not read.
SPLIT_FEE = """
            <Ntry>
                <Amt Ccy="EUR">7.00</Amt>
                <CdtDbtInd>DBIT</CdtDbtInd>
                <Sts>BOOK</Sts>
                <BookgDt><Dt>2026-04-30</Dt></BookgDt>
                <NtryDtls><TxDtls>
                    <Refs><AcctSvcrRef>VP26043087435186</AcctSvcrRef></Refs>
                </TxDtls></NtryDtls>
                <NtryDtls><TxDtls>
                    <Refs><AcctSvcrRef>523336831</AcctSvcrRef></Refs>
                    <AmtDtls><InstdAmt><Amt Ccy="EUR">7.00</Amt></InstdAmt></AmtDtls>
                    <AddtlTxInf>Tatra Business</AddtlTxInf>
                </TxDtls></NtryDtls>
            </Ntry>"""

# A real batch: two payments in one entry, each with its own amount.
BATCH = """
            <Ntry>
                <Amt Ccy="EUR">300.00</Amt>
                <CdtDbtInd>CRDT</CdtDbtInd>
                <Sts>BOOK</Sts>
                <BookgDt><Dt>2026-04-10</Dt></BookgDt>
                <NtryDtls>
                    <TxDtls>
                        <Refs><EndToEndId>/VS1001/SS/KS</EndToEndId></Refs>
                        <AmtDtls><TxAmt><Amt Ccy="EUR">100.00</Amt></TxAmt></AmtDtls>
                    </TxDtls>
                    <TxDtls>
                        <Refs><EndToEndId>/VS1002/SS/KS</EndToEndId></Refs>
                        <AmtDtls><TxAmt><Amt Ccy="EUR">200.00</Amt></TxAmt></AmtDtls>
                    </TxDtls>
                </NtryDtls>
            </Ntry>"""


def _balance(code, amount, day=None):
    date = "<Dt><Dt>2026-04-%02d</Dt></Dt>" % day if day else ""
    return BALANCE.format(code=code, amount=amount, date=date)


@tagged("post_install", "-at_install")
class TestDailyBalances(TransactionCase):

    def _parse(self, *balances, entries=SIMPLE_ENTRY):
        data = STATEMENT.format(balances="".join(balances), entries=entries).encode()
        _currency, _account, statements = self.env[
            "account.statement.import.camt.parser"].parse(data)
        return statements[0]

    def test_the_month_closes_on_its_last_day(self):
        """Tatra banka: one OPBD, then a CLBD for each day with movements."""
        statement = self._parse(
            _balance("OPBD", "19096.35", 1),
            _balance("CLBD", "8626.28", 1),
            _balance("CLBD", "43907.53", 29),
            _balance("CLBD", "43707.47", 30),
        )
        self.assertAlmostEqual(statement["balance_start"], 19096.35)
        self.assertAlmostEqual(statement["balance_end_real"], 43707.47)

    def test_the_latest_date_wins_not_the_document_order(self):
        statement = self._parse(
            _balance("OPBD", "100.00", 1),
            _balance("CLBD", "300.00", 30),
            _balance("CLBD", "200.00", 15),
        )
        self.assertAlmostEqual(statement["balance_end_real"], 300.00)

    def test_undated_balances_keep_the_document_order(self):
        statement = self._parse(
            _balance("OPBD", "100.00"),
            _balance("CLBD", "150.00"),
            _balance("CLBD", "175.00"),
        )
        self.assertAlmostEqual(statement["balance_end_real"], 175.00)

    def test_a_single_closing_balance_is_untouched(self):
        statement = self._parse(
            _balance("OPBD", "100.00", 1),
            _balance("CLBD", "200.00", 30),
        )
        self.assertAlmostEqual(statement["balance_start"], 100.00)
        self.assertAlmostEqual(statement["balance_end_real"], 200.00)

    def test_one_transaction_in_two_detail_blocks_is_one_line(self):
        statement = self._parse(
            _balance("OPBD", "100.00", 1), _balance("CLBD", "93.00", 30),
            entries=SPLIT_FEE)
        lines = statement["transactions"]
        self.assertEqual(len(lines), 1, "the fee was booked once per detail block")
        self.assertAlmostEqual(lines[0]["amount"], -7.00)
        self.assertAlmostEqual(
            statement["balance_start"] + sum(t["amount"] for t in lines),
            statement["balance_end_real"])

    def test_a_batch_keeps_a_line_per_payment(self):
        statement = self._parse(
            _balance("OPBD", "100.00", 1), _balance("CLBD", "400.00", 30),
            entries=BATCH)
        self.assertEqual(
            sorted(t["amount"] for t in statement["transactions"]), [100.00, 200.00])
