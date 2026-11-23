# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Several worked-day lines of one payroll code, read by the rules as one.

Both payroll engines hand the salary rules one worked-day line per code. A
payslip can hold several lines of a code: on the Community engine each leave
type has a line of its own and several leave types share a Slovak payroll
code; on the Enterprise engine each work entry type has a line, and a type
without a country may repeat a Slovak code; on either a line can be added by
hand. One line then hides the others, and an absence is deducted or
compensated for one of them only.

``worked_day_totals`` gives the rules, for such a code, one object that
holds the days and hours of all its lines. A code with one line stays that
line.
"""


class WorkedDayTotal:
    """The worked-day lines of one code, read as one line.

    Its days and hours are those of all the lines together, and on the
    Enterprise engine, whose lines carry it, their amount too; anything else
    is read from the first of them.
    """

    __slots__ = ("_lines",)

    # Added up where the engine's line has the field.
    SUMMED = ("number_of_days", "number_of_hours", "amount")

    def __init__(self, lines):
        self._lines = lines

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        if name in self.SUMMED and name in self._lines._fields:
            return sum(self._lines.mapped(name))
        return getattr(self._lines[:1], name)

    def __getitem__(self, name):
        return getattr(self, name)


def worked_day_totals(lines):
    """``{code: the lines as one}`` for each code with several ``lines``."""
    return {
        code: WorkedDayTotal(code_lines)
        for code, code_lines in lines.filtered("code").grouped("code").items()
        if len(code_lines) > 1
    }
