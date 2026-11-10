# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""One "meals abroad" switch per day became one per meal.

The old column stays in the table after the field is gone, so its value is
copied to the three new flags; the stored amounts do not change, since every
meal of the day still counts on the same side.
"""


def migrate(cr, version):
    cr.execute("""
        SELECT 1 FROM information_schema.columns
         WHERE table_name = 'l10n_sk_travel_order_day' AND column_name = 'meals_abroad'
    """)
    if not cr.fetchone():
        return
    cr.execute("""
        UPDATE l10n_sk_travel_order_day
           SET breakfast_abroad = meals_abroad,
               lunch_abroad = meals_abroad,
               dinner_abroad = meals_abroad
         WHERE meals_abroad
    """)
