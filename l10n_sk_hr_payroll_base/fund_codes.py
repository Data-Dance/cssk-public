# Copyright 2026 Data Dance s.r.o., votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Stable social fund names shared by rules, readers and monthly annexes."""

SOCIAL_FUNDS = {
    "SICK": ("sickness", "employee"),
    "PENSION": ("pension", "employee"),
    "DISABILITY": ("disability", "employee"),
    "UNEMPLOYMENT": ("unemployment", "employee"),
    "SICKEMPLOYER": ("sickness", "employer"),
    "PENSIONEMPLOYER": ("pension", "employer"),
    "DISABILITYEMPLOYER": ("disability", "employer"),
    "UNEMPLOYMENTEMPLOYER": ("unemployment", "employer"),
    "SHORTTIMEEMPLOYER": ("shorttime", "employer"),
    "GUARANTEEEMPLOYER": ("guarantee", "employer"),
    "ACCIDENT": ("accident", "employer"),
    "RESERVEFUNDEMPLOYER": ("reserve", "employer"),
}
