# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging

from odoo import models

_logger = logging.getLogger(__name__)

SK_CLOSING_ACCOUNT_CODE = "702000"  # Konečný účet súvahový
SK_OPENING_ACCOUNT_CODE = "701000"  # Začiatočný účet súvahový


class AccountFiscalyearClosingConfig(models.Model):
    _inherit = "account.fiscalyear.closing.config"

    def _l10n_sk_is_sk(self):
        self.ensure_one()
        return self.fyc_id.company_id.chart_template == "sk"

    def _mapping_move_lines_get(self):
        """Mirror every closed account on the závierkový účet, not just the net.

        The generic engine posts ONE destination line carrying the *net* of all
        source accounts. On a complete balance sheet that net is zero, so 702
        would not appear in the entry at all — the assets would simply be
        contra-posed against the liabilities. Mechanically balanced, but it is
        not the Slovak závierka: 702 *Konečný účet súvahový* is precisely the
        account every súvahový účet is closed against, and it must carry the
        counter-entry for each of them (its own total then being zero by the
        bilančná rovnosť, not by omission).

        So for SK we pair each source line with its mirror on the destination.
        """
        move_lines = super()._mapping_move_lines_get()
        if not self._l10n_sk_is_sk():
            return move_lines

        dest_ids = {m.dest_account_id.id for m in self.mapping_ids if m.dest_account_id}
        if not dest_ids:
            return move_lines

        # Each mapping has its own destination, so resolve source account ->
        # destination per mapping rather than assuming a single one. Our SK
        # template does use one destination per config, but a hand-edited
        # closing may not, and mirroring everything onto the first mapping's
        # destination would post a plausible-but-wrong allocation.
        dest_by_source = {}
        for mapping in self.mapping_ids.filtered("dest_account_id"):
            src_accounts = self.env["account.account"].search(
                [
                    ("company_ids", "in", self.fyc_id.company_id.ids),
                    ("code", "=ilike", mapping.src_accounts),
                ]
            )
            for account in src_accounts:
                dest_by_source.setdefault(account.id, mapping.dest_account_id)

        # Drop the engine's netted destination line(s); we re-emit per account.
        source_lines = [line for line in move_lines if line.get("account_id") not in dest_ids]

        mirrored = []
        for line in source_lines:
            mirrored.append(line)
            dest_account = dest_by_source.get(line.get("account_id"))
            if not dest_account:
                # No mapping claims this account: leave the engine's own
                # balancing behaviour alone rather than inventing a counterpart.
                continue
            counter = dict(
                line,
                account_id=dest_account.id,
                debit=line.get("credit") or 0.0,
                credit=line.get("debit") or 0.0,
            )
            # Only carry amount_currency when the source line actually had one.
            # Passing amount_currency=0 on a line with no foreign currency makes
            # Odoo derive the balance FROM it and zero the line, silently
            # unbalancing the entry.
            if line.get("amount_currency"):
                counter["amount_currency"] = -line["amount_currency"]
            else:
                counter.pop("amount_currency", None)
            mirrored.append(counter)
        return mirrored

    def inverse_move_prepare(self):
        """Reopen through 701, not through 702.

        The engine builds the opening move by plainly reversing the closing one,
        which would leave **702** as the counterpart on both sides. Slovak
        practice uses a matching pair — the year closes on *Konečný účet
        súvahový* (702) and reopens on *Začiatočný účet súvahový* (701) — so the
        counterpart is swapped here, on the freshly reversed draft move.
        """
        move_ids = super().inverse_move_prepare()
        if not move_ids or self.move_type != "opening":
            return move_ids
        company = self.fyc_id.company_id
        if company.chart_template != "sk":
            return move_ids

        Account = self.env["account.account"]
        closing_account = Account.search(
            [("company_ids", "in", company.ids), ("code", "=", SK_CLOSING_ACCOUNT_CODE)],
            limit=1,
        )
        opening_account = Account.search(
            [("company_ids", "in", company.ids), ("code", "=", SK_OPENING_ACCOUNT_CODE)],
            limit=1,
        )
        if not (closing_account and opening_account):
            _logger.warning(
                "SK závierka: účet %s alebo %s chýba, otvorenie zostáva na 702.",
                SK_CLOSING_ACCOUNT_CODE,
                SK_OPENING_ACCOUNT_CODE,
            )
            return move_ids

        lines = (
            self.env["account.move"]
            .browse(move_ids)
            .line_ids.filtered(lambda line: line.account_id == closing_account)
        )
        if lines:
            lines.account_id = opening_account
        return move_ids
