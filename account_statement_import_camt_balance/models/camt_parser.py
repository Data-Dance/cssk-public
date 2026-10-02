# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Two ways a CAMT.053 that is correct fails the balance check on import.

**A balance per day.**

Tatra banka's monthly CAMT.053 carries one OPBD for the month and a CLBD for
every day with movements (24 in one April file). The OCA parser takes the FIRST
node of each code, so the statement "closes" on the first day's balance and
every import fails the balance check. The opening balance is the earliest
OPBD/PRCD, and the closing balance the latest CLBD, by date where the nodes carry
one and by document order where they do not.

**One transaction told in several detail blocks.** The OCA parser yields a line
per ``TxDtls``, and a block without its own ``Amt`` / ``TxAmt`` inherits the
whole entry amount. Tatra banka writes a fee as one block with references and
one with the amount in ``InstdAmt``, so the fee is booked twice. The lines of
an entry must add up to the entry. When they do not, the blocks describe one
transaction and become one line. A batch whose blocks carry their own amounts
and add up is left as it is.
"""

from odoo import models
from odoo.tools import float_compare

_XPATH = './ns:Bal/ns:Tp/ns:CdOrPrtry/ns:Cd[text()="%s"]/../../..'


class CamtParser(models.AbstractModel):
    _inherit = "account.statement.import.camt.parser"

    def _balance_date(self, ns, balance_node):
        found = balance_node.xpath(
            "./ns:Dt/ns:Dt/text() | ./ns:Dt/ns:DtTm/text()", namespaces={"ns": ns})
        return found[0][:10] if found else ""

    def _balance_nodes(self, ns, node, codes):
        nodes = []
        for code in codes:
            nodes += node.xpath(_XPATH % code, namespaces={"ns": ns})
        # Stable: nodes without a date keep their document order.
        return sorted(nodes, key=lambda n: self._balance_date(ns, n))

    def get_balance_amounts(self, ns, node):
        start, end = super().get_balance_amounts(ns, node)
        openings = self._balance_nodes(ns, node, ("OPBD", "PRCD"))
        if len(openings) > 1:
            start = self.parse_amount(ns, openings[0])
        closings = self._balance_nodes(ns, node, ("CLBD",))
        if len(closings) > 1:
            end = self.parse_amount(ns, closings[-1])
        return start, end

    def parse_entry(self, ns, node):
        transactions = list(super().parse_entry(ns, node))
        if len(transactions) < 2:
            yield from transactions
            return
        amount = self.parse_amount(ns, node)
        total = sum(t.get("amount", 0.0) for t in transactions)
        if not float_compare(total, amount, precision_digits=2):
            yield from transactions
            return
        merged = dict(transactions[0])
        for transaction in transactions[1:]:
            for key, value in transaction.items():
                if value and not merged.get(key):
                    merged[key] = value
        narrations = [t.get("narration") for t in transactions if t.get("narration")]
        if narrations:
            merged["narration"] = "\n".join(dict.fromkeys(narrations))
        merged["amount"] = amount
        yield merged
