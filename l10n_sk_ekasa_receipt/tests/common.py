# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import json
import os

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")

# The QR payloads that resolve to the fixtures. See fixtures/README.rst:
# the amounts and structure are from real service responses, the
# identities and identifiers are synthetic.
QR_ONLINE_FUEL = "O-ABCDEF0000000002ABCDEF0000000002"
QR_OFFLINE_RESTAURANT = (
    "AAAA0001-BBBB0002-CCCC0003-DDDD0004-EEEE0005"
    ":88820990000020004:260314195902:5:181.90")


def load_fixture(name):
    """A response from Finančná správa's verification service.

    Structure and figures verbatim; identities anonymised. See
    ``fixtures/README.rst``.
    """
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as handle:
        return json.load(handle)
