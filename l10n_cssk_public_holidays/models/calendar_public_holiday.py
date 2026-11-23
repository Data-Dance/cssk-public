# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Slovak and Czech days of rest for the OCA public holiday calendar.

Only days of rest (dni pracovného pokoja / dny pracovního klidu) are
generated, because that is what leave counting and attendance need. A
public holiday that the law makes a working day for a given year (Slovakia
2026: 8 May, 15 September; 17 November from 2025) is therefore left out of
that year, while payroll still treats it as a holiday on its own rules.

Sources: SK zákon č. 241/1993 Z. z. as amended by 261/2025 Z. z. (effective
1. 11. 2025); CZ zákon č. 245/2000 Sb.

The working calendars
---------------------
Time Off and both payroll engines know a public holiday only as a public
holiday of the working calendars: a ``resource.calendar.leaves`` record with
no resource. The lines of the countries named by the system parameter
``l10n_cssk_public_holidays.calendar_leave_countries`` (default ``SK``) are
therefore kept as such records, one per company of the country and holiday,
with no working calendar set, so that every calendar of the company has it.
"""
from datetime import date, datetime, time, timedelta

import pytz
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models

# Countries whose holidays go into the working calendars, comma separated.
LEAVE_COUNTRIES_PARAM = "l10n_cssk_public_holidays.calendar_leave_countries"
LEAVE_COUNTRIES_DEFAULT = "SK"
# The day of rest is a calendar day of the country.
COUNTRY_TZ = {"SK": "Europe/Bratislava", "CZ": "Europe/Prague"}
# Context key: lines created in bulk wait for ``cssk_sync_calendar_leaves``.
NO_LEAVES_KEY = "cssk_no_calendar_leaves"
CRON_XMLID = "l10n_cssk_public_holidays.ir_cron_cssk_public_holidays"
# Whole calendar months before the current one that the working calendars
# are kept for unasked. Payroll for a month is computed early in the next
# one, so the month just ended is still open and needs its holidays.
OPEN_MONTHS_BACK = 1

# (month, day, name, from_year, to_year, skipped_years)
# from_year / to_year are inclusive bounds; None means open.
SK_FIXED = [
    (1, 1, "Deň vzniku Slovenskej republiky", None, None, ()),
    (1, 6, "Zjavenie Pána (Traja králi)", None, None, ()),
    (5, 1, "Sviatok práce", None, None, ()),
    (5, 8, "Deň víťazstva nad fašizmom", None, None, (2026,)),
    (7, 5, "Sviatok svätého Cyrila a svätého Metoda", None, None, ()),
    (8, 29, "Výročie Slovenského národného povstania", None, None, ()),
    (9, 1, "Deň Ústavy Slovenskej republiky", None, 2023, ()),
    (9, 15, "Sedembolestná Panna Mária", None, None, (2026,)),
    (11, 1, "Sviatok všetkých svätých", None, None, ()),
    (11, 17, "Deň boja za slobodu a demokraciu", None, 2024, ()),
    (12, 24, "Štedrý deň", None, None, ()),
    (12, 25, "Prvý sviatok vianočný", None, None, ()),
    (12, 26, "Druhý sviatok vianočný", None, None, ()),
]
SK_EASTER = [(-2, "Veľký piatok"), (1, "Veľkonočný pondelok")]

CZ_FIXED = [
    (1, 1, "Den obnovy samostatného českého státu, Nový rok", None, None, ()),
    (5, 1, "Svátek práce", None, None, ()),
    (5, 8, "Den vítězství", None, None, ()),
    (7, 5, "Den slovanských věrozvěstů Cyrila a Metoděje", None, None, ()),
    (7, 6, "Den upálení mistra Jana Husa", None, None, ()),
    (9, 28, "Den české státnosti", None, None, ()),
    (10, 28, "Den vzniku samostatného československého státu", None, None, ()),
    (11, 17, "Den boje za svobodu a demokracii", None, None, ()),
    (12, 24, "Štědrý den", None, None, ()),
    (12, 25, "1. svátek vánoční", None, None, ()),
    (12, 26, "2. svátek vánoční", None, None, ()),
]
CZ_EASTER = [(-2, "Velký pátek", 2016), (1, "Velikonoční pondělí", None)]

RULES = {
    "SK": (SK_FIXED, [(d, n, None) for d, n in SK_EASTER]),
    "CZ": (CZ_FIXED, CZ_EASTER),
}


def easter_sunday(year):
    """Gregorian Easter Sunday (Meeus/Jones/Butcher)."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    L = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * L) // 451
    month, day = divmod(h + L - 7 * m + 114, 31)
    return date(year, month, day + 1)


def days_of_rest(country_code, year):
    """Return [(date, name, variable)] of the days of rest for one year."""
    fixed, easter = RULES[country_code]
    out = []
    for month, day, name, from_year, to_year, skipped in fixed:
        if from_year and year < from_year or to_year and year > to_year or year in skipped:
            continue
        out.append((date(year, month, day), name, False))
    sunday = easter_sunday(year)
    for offset, name, from_year in easter:
        if from_year and year < from_year:
            continue
        out.append((sunday + timedelta(days=offset), name, True))
    return sorted(out)


class CalendarPublicHoliday(models.Model):
    _inherit = "calendar.public.holiday"

    @api.model
    def cssk_generate(self, years, country_codes=("SK", "CZ")):
        """Create or complete the public holiday record of each year and country.

        Idempotent: lines already present (same date) are kept, including any
        manual edits, and only missing days are added. Returns the records.
        """
        Line = self.env["calendar.public.holiday.line"]
        records = self.browse()
        for code in country_codes:
            country = self.env["res.country"].search([("code", "=", code)], limit=1)
            if not country:
                continue
            for year in years:
                holiday = self.search(
                    [("year", "=", year), ("country_id", "=", country.id)], limit=1
                )
                if not holiday:
                    holiday = self.create({"year": year, "country_id": country.id})
                # Nationwide lines only: a regional line on the same date does
                # not make the day of rest a nationwide one.
                existing = set(
                    holiday.line_ids.filtered(lambda line: not line.state_ids).mapped("date")
                )
                # A year is generated in bulk; ``cssk_sync_calendar_leaves``
                # puts its days into the working calendars.
                Line.with_context(**{NO_LEAVES_KEY: True}).create(
                    [
                        {
                            "public_holiday_id": holiday.id,
                            "date": day,
                            "name": name,
                            "variable_date": variable,
                        }
                        for day, name, variable in days_of_rest(code, year)
                        if day not in existing
                    ]
                )
                records |= holiday
        return records

    @api.model
    def _cssk_default_sync_start(self):
        """The first day of the earliest month still open for payroll."""
        return date.today().replace(day=1) - relativedelta(months=OPEN_MONTHS_BACK)

    @api.model
    def _cssk_kept_years(self):
        """The years kept present: the open months, this year and the next."""
        year = date.today().year
        return tuple(range(self._cssk_default_sync_start().year, year + 2))

    @api.model
    def cssk_generate_next_year(self):
        """Cron entry point: keep the current and the next year present."""
        records = self.cssk_generate(years=self._cssk_kept_years())
        # Also reaches a company created since the last run.
        self.cssk_sync_calendar_leaves()
        return records

    @api.model
    def cssk_run_scheduled_action_soon(self):
        """Ask the scheduled action to run at once.

        For the install hook and the upgrade: while modules are loading,
        Time Off and payroll may not be in the registry yet, and a public
        holiday written then would not make them recount what spans it.
        """
        cron = self.env.ref(CRON_XMLID, raise_if_not_found=False)
        if cron:
            cron._trigger()
        return bool(cron)

    @api.model
    def cssk_sync_calendar_leaves(self, date_from=None):
        """Bring the working calendars in line with the holiday lines.

        Covers the lines dated ``date_from`` or later; when not given, from
        the first day of the previous calendar month. A public holiday that
        is new to a company makes Time Off recount the leave that spans it;
        one that is already there is not written again. Pass an earlier day
        to put older holidays into the calendars as well.
        """
        date_from = date_from or self._cssk_default_sync_start()
        lines = self.env["calendar.public.holiday.line"].search(
            [
                ("date", ">=", date_from),
                ("public_holiday_id.country_id.code", "in", list(RULES)),
            ]
        )
        lines._cssk_sync_calendar_leaves()
        return True

    def write(self, vals):
        res = super().write(vals)
        if "country_id" in vals:
            self.line_ids._cssk_sync_calendar_leaves()
        return res

    def unlink(self):
        # The lines go by database cascade, which would skip their leaves.
        self.line_ids._cssk_calendar_leaves().unlink()
        return super().unlink()


class CalendarPublicHolidayLine(models.Model):
    _inherit = "calendar.public.holiday.line"

    @api.model
    def _cssk_leave_countries(self):
        """Codes of the countries whose holidays go into the working calendars."""
        value = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(LEAVE_COUNTRIES_PARAM, LEAVE_COUNTRIES_DEFAULT)
        )
        codes = {code.strip().upper() for code in (value or "").split(",")}
        return codes & set(RULES)

    def _cssk_calendar_leaves(self):
        """The public holidays of the working calendars kept for these lines."""
        return (
            self.env["resource.calendar.leaves"]
            .sudo()
            .search([("l10n_cssk_public_holiday_line_id", "in", self.ids)])
        )

    @api.model
    def _cssk_day_bounds(self, day, country_code):
        """The calendar day in the country, as naive UTC datetimes."""
        tz = pytz.timezone(COUNTRY_TZ[country_code])

        def to_utc(moment):
            local = tz.localize(datetime.combine(day, moment))
            return local.astimezone(pytz.utc).replace(tzinfo=None)

        return to_utc(time.min), to_utc(time(23, 59, 59))

    def _cssk_sync_calendar_leaves(self):
        """Create, move, rename or remove the calendar leaves of these lines.

        One public holiday per company of the line's country, for every
        working calendar of the company. A nationwide line of an enabled
        country has one; any other line has none. A day on which the company
        already has a public holiday of its own is left to that record.
        """
        Leave = self.env["resource.calendar.leaves"].sudo()
        countries = self._cssk_leave_countries()
        companies = {}
        for line in self.sudo():
            code = line.public_holiday_id.country_id.code
            wanted = self.env["res.company"].sudo()
            if code in countries and not line.state_ids:
                if code not in companies:
                    companies[code] = wanted.search(
                        [("partner_id.country_id.code", "=", code)]
                    )
                wanted = companies[code]
            leaves = line._cssk_calendar_leaves()
            kept = leaves.filtered(lambda leave: leave.company_id in wanted)
            (leaves - kept).unlink()
            if not wanted:
                continue
            start, stop = self._cssk_day_bounds(line.date, code)
            by_company = kept.grouped("company_id")
            for company in wanted:
                mine = by_company.get(company, Leave.browse())
                if mine[1:] or (mine.date_from, mine.date_to) != (start, stop):
                    # A moved leave is written anew: a change of its dates
                    # has its company computed again, as the active one.
                    mine.unlink()
                    mine = Leave.browse()
                if mine:
                    if mine.name != line.name:
                        mine.name = line.name
                    continue
                if Leave.search_count(
                    [
                        ("resource_id", "=", False),
                        ("company_id", "=", company.id),
                        ("date_from", "<=", stop),
                        ("date_to", ">=", start),
                    ],
                    limit=1,
                ):
                    continue
                leave = Leave.with_company(company).create(
                    {
                        "name": line.name,
                        "calendar_id": False,
                        "resource_id": False,
                        "date_from": start,
                        "date_to": stop,
                        "time_type": "leave",
                        "l10n_cssk_public_holiday_line_id": line.id,
                    }
                )
                # Without a calendar the company is computed as the active
                # one, whenever that happens to be computed.
                if leave.company_id != company:
                    leave.company_id = company

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        if not self.env.context.get(NO_LEAVES_KEY):
            lines._cssk_sync_calendar_leaves()
        return lines

    def write(self, vals):
        res = super().write(vals)
        if {"date", "name", "state_ids", "public_holiday_id"} & set(vals):
            self._cssk_sync_calendar_leaves()
        return res

    def unlink(self):
        self._cssk_calendar_leaves().unlink()
        return super().unlink()


class ResourceCalendarLeaves(models.Model):
    _inherit = "resource.calendar.leaves"

    l10n_cssk_public_holiday_line_id = fields.Many2one(
        "calendar.public.holiday.line",
        string="Public Holiday Line",
        ondelete="cascade",
        index="btree_not_null",
        copy=False,
        readonly=True,
        help="The line of the public holiday calendar this public holiday of "
        "the working calendars is kept for. It follows the line when the "
        "line is renamed, moved or removed.",
    )
