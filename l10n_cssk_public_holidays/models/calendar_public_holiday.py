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
"""
from datetime import date, timedelta

from odoo import api, models

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
                Line.create(
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
    def cssk_generate_next_year(self):
        """Cron entry point: keep the current and the next year present."""
        year = date.today().year
        return self.cssk_generate(years=(year, year + 1))
