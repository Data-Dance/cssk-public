# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Forget the cached register answers that predate the legal form.

A row cached before this version has no legal form and reads as "not a
natural person", which is an answer nobody gave. Left alone it would be
served for the rest of its day, and a sole trader signing up in that window
would be taken for a company. The cache is only a cache: the next question
asks the register again.
"""


def migrate(cr, version):
    if not version:
        return
    cr.execute("DELETE FROM cssk_registry_lookup WHERE outcome = 'verified'")
