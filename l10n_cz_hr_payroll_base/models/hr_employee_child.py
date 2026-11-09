# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The children an employee claims the child tax benefit for (§ 35c ZDP).

One record per child: who the child is, the order the benefit is claimed in,
ZTP/P, and optionally the period of the claim. The payslip, the annual tax
reconciliation and the monthly employer report (JMHZ) all read the month's
children from here, so the three cannot disagree.

Without any record the payroll falls back to the counts on the contract
(``l10n_cz_children_t1``/``t2``/``t3``, ``l10n_cz_children_ztpp``), which
cannot say in which months a child was claimed.
"""

import calendar
from datetime import date

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from .hr_version import CZ_PAYROLL_GROUP

CHILD_ORDERS = [
    ("1", "1 – first child"),
    ("2", "2 – second child"),
    ("3", "3 – third and further child"),
    ("N", "N – not claimed"),
]


def birth_number_date(birth_number):
    """The date of birth a Czech birth number encodes, or None.

    YYMMDD: the month carries +50 for a woman and, from 2004, +20 when the
    day's numbers ran out; nine digits are births before 1954, ten digits
    born 1954 and later (a two-digit year below 54 is then 20YY).
    """
    digits = "".join(ch for ch in (birth_number or "") if ch.isdigit())
    if len(digits) not in (9, 10):
        return None
    yy, mm, dd = int(digits[0:2]), int(digits[2:4]), int(digits[4:6])
    for shift in (70, 50, 20, 0):
        if mm > shift:
            mm -= shift
            break
    if len(digits) == 9:
        year = 1900 + yy
    else:
        year = 2000 + yy if yy < 54 else 1900 + yy
    try:
        return date(year, mm, dd)
    except ValueError:
        return None


class L10nCzEmployeeChild(models.Model):
    _name = "l10n.cz.employee.child"
    _description = "Child maintained by a Czech employee (tax benefit)"
    _order = "employee_id, sequence, id"

    employee_id = fields.Many2one("hr.employee", required=True,
                                  ondelete="cascade", index=True)
    sequence = fields.Integer(default=10)
    first_name = fields.Char("First name", required=True)
    surname = fields.Char(required=True)
    birthday = fields.Date("Date of birth")
    birth_number = fields.Char("Birth number")
    ztpp = fields.Boolean(
        "ZTP/P holder",
        help="The child holds a ZTP/P card: the benefit for the child is "
             "doubled (§ 35c odst. 7 ZDP).")
    order = fields.Selection(
        CHILD_ORDERS, "Order (tax benefit)", required=True, default="1",
        help="The order the employee claims the benefit in — 1, 2, 3 for the "
             "third and every further child — or N for a child maintained "
             "in the household but not claimed by this employee. The "
             "employee chooses the order; it need not follow age.")
    date_from = fields.Date(
        "Claimed from",
        help="Leave empty to claim from the month of birth. Otherwise a day "
             "of the first month the benefit is due (§ 35c odst. 10 ZDP): the "
             "month of adoption, of placement into care replacing the "
             "parents' or of the start of studies counts itself; any other "
             "start (the child came to the household, the other parent "
             "stopped claiming) counts from the next month, so enter the "
             "first day of that month.")
    date_to = fields.Date(
        "Claimed to",
        help="Last day the conditions are met: the child left the household, "
             "ended their studies, or the other parent claims from the next "
             "month. The month of that day is still claimed.")

    @api.constrains("birthday", "birth_number")
    def _check_identification(self):
        for child in self:
            digits = "".join(c for c in (child.birth_number or "")
                             if c.isdigit())
            if child.birth_number and not 9 <= len(digits) <= 10:
                raise ValidationError(self.env._(
                    "The birth number of %(child)s must have 9 or 10 digits.",
                    child="%s %s" % (child.first_name, child.surname)))

    @api.constrains("date_from", "date_to")
    def _check_claim_period(self):
        for child in self:
            if child.date_from and child.date_to and child.date_to < child.date_from:
                raise ValidationError(self.env._(
                    "The claim period of %(child)s ends before it starts.",
                    child="%s %s" % (child.first_name, child.surname)))

    def _l10n_cz_claim_span(self):
        """(first day, last day) of the claim; None for an open end."""
        self.ensure_one()
        starts = [d for d in (self._l10n_cz_birth_date(), self.date_from) if d]
        return (max(starts) if starts else None, self.date_to or None)

    @api.constrains("order", "birthday", "birth_number", "date_from",
                    "date_to", "employee_id")
    def _check_order_unique(self):
        """One first and one second child at a time: two children claimed as
        the first in the same months would both get the first child's
        amount. The third order is "the third and every further child"."""
        for employee in self.employee_id:
            kids = employee.l10n_cz_child_ids.filtered(
                lambda c: c.order in ("1", "2"))
            for i, one in enumerate(kids):
                a1, b1 = one._l10n_cz_claim_span()
                for two in kids[i + 1:]:
                    if two.order != one.order:
                        continue
                    a2, b2 = two._l10n_cz_claim_span()
                    if (a1 is None or b2 is None or a1 <= b2) and (
                            a2 is None or b1 is None or a2 <= b1):
                        raise ValidationError(self.env._(
                            "%(one)s and %(two)s are both claimed as child "
                            "%(order)s for the same months. Give one of them "
                            "the next order, or end one claim before the "
                            "other starts.",
                            one="%s %s" % (one.first_name, one.surname),
                            two="%s %s" % (two.first_name, two.surname),
                            order=one.order))

    def _l10n_cz_birth_date(self):
        self.ensure_one()
        return self.birthday or birth_number_date(self.birth_number)

    def _l10n_cz_maintained_in(self, year, month):
        """Whether the conditions of the benefit hold for the child in the
        month, whatever the order (``N`` included).

        § 35c odst. 10 ZDP: "1/12 za každý kalendářní měsíc, na jehož počátku
        byly splněny podmínky pro jeho uplatnění. Daňové zvýhodnění lze
        uplatnit již v kalendářním měsíci, ve kterém se dítě narodilo, nebo ve
        kterém začíná soustavná příprava dítěte na budoucí povolání, anebo ve
        kterém bylo dítě osvojeno nebo převzato do péče nahrazující péči
        rodičů". The month of birth follows from the date of birth; which of
        the other starts applies only the user knows, so *Claimed from* names
        the first month that counts. A claim ending during a month keeps that
        month: the conditions were met on its first day.
        """
        self.ensure_one()
        first = date(year, month, 1)
        last = date(year, month, calendar.monthrange(year, month)[1])
        born = self._l10n_cz_birth_date()
        if born and born > last:
            return False
        if self.date_from and self.date_from > last:
            return False
        if self.date_to and self.date_to < first:
            return False
        return True

    def _l10n_cz_claimed_in(self, year, month):
        """Whether this employee claims the benefit for the child in the
        month: maintained and not marked ``N``."""
        self.ensure_one()
        return self.order != "N" and self._l10n_cz_maintained_in(year, month)
