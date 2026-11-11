# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Keep installed res.bank records in step with the registries.

The data files are ``noupdate="1"``, and they have to be: with noupdate off, a
bank that leaves the registry would lose its xmlid on the next upgrade and
Odoo's ``_process_end`` would delete it — and ``res.partner.bank.bank_id``
would quietly become empty on every account that pointed at it. But noupdate
also means an upgrade never rewrites a changed record, so a corrected BIC
(Fio SK was ``FIOZSKBAX``, nine characters) would never reach a database that
already has the bank.

So the XML only creates, and these functions do the rest:

``adopt_existing_banks``
    Before the data loads, binds a bank that already exists without our xmlid
    (typed in by hand, or created by ``base_bank_from_iban`` from schwifty's
    table) to the xmlid of the same code and country, so the load does not
    create a second Tatra banka next to the first.

``sync_registry``
    After the data loads, writes the registry-owned fields — name, code,
    BIC, country — onto every record we ship, and archives the records whose
    code left the registry. Archived, never deleted: accounts keep pointing at
    them, and nothing new can pick them. A BIC the registry does not publish is
    never cleared here, because an empty cell is an absence of information,
    not a statement that the bank has none.

Both run on install (pre/post init hooks) and on every version change
(``migrations/0.0.0``), which is what a regenerated data set comes with.
"""

import logging
import re

from lxml import etree

from odoo.tools.misc import file_path

_logger = logging.getLogger(__name__)

MODULE = "l10n_cssk_banks"
DATA_FILES = ("data/res_bank_cz.xml", "data/res_bank_sk.xml")
#: The fields the registries are authoritative for. Address, phone and e-mail
#: are not published by either registry and stay whatever the user made them.
SYNCED_FIELDS = ("name", "code", "bic", "country")
#: Only xmlids of this shape are ever archived for having left the registry.
#: Anything else under our module (a leftover of the rename whose bank had been
#: moved to a third country, say) is not ours to judge and is left alone.
SHIPPED_XMLID = re.compile(r"^bank_(cz|sk)_\d{4}$")


def shipped_banks():
    """``{xmlid name: {name, code, bic, country_code}}`` as the data files say."""
    banks = {}
    for rel in DATA_FILES:
        tree = etree.parse(file_path(f"{MODULE}/{rel}"))
        for rec in tree.iter("record"):
            vals = {"bic": False}
            for field in rec.iter("field"):
                if field.get("name") == "country":
                    vals["country_code"] = field.get("ref").split(".")[-1].upper()
                else:
                    vals[field.get("name")] = (field.text or "").strip() or False
            banks[rec.get("id")] = vals
    return banks


def _countries(env, banks):
    codes = {b["country_code"] for b in banks.values()}
    return {c.code: c for c in env["res.country"].search([("code", "in", list(codes))])}


def _our_xmlids(env):
    return {
        imd.name: imd
        for imd in env["ir.model.data"].sudo().search(
            [("module", "=", MODULE), ("model", "=", "res.bank")])
    }


def adopt_existing_banks(env):
    banks = shipped_banks()
    countries = _countries(env, banks)
    ours = _our_xmlids(env)
    bound = {imd.res_id for imd in ours.values()}
    Bank = env["res.bank"].sudo().with_context(active_test=False)
    Account = env["res.partner.bank"].sudo().with_context(active_test=False)
    adopted = []
    for name, vals in sorted(banks.items()):
        if name in ours:
            continue
        country = countries.get(vals["country_code"])
        if not country:
            continue  # never match on "no country"
        candidates = Bank.search([
            ("code", "=", vals["code"]),
            ("country", "=", country.id),
            ("id", "not in", list(bound)),
        ])
        if not candidates:
            continue
        # The one partners actually use, then an active one, then the oldest.
        best = max(candidates, key=lambda b: (
            Account.search_count([("bank_id", "=", b.id)]), b.active, -b.id))
        env["ir.model.data"].sudo().create({
            "module": MODULE, "name": name, "model": "res.bank",
            "res_id": best.id, "noupdate": True,
        })
        bound.add(best.id)
        adopted.append(f"{name}=res.bank({best.id})")
    if adopted:
        _logger.info("%s: adopted %d existing bank(s): %s",
                     MODULE, len(adopted), ", ".join(adopted))
    return adopted


def sync_registry(env):
    banks = shipped_banks()
    countries = _countries(env, banks)
    ours = _our_xmlids(env)
    Bank = env["res.bank"].sudo().with_context(active_test=False)
    changed, archived = [], []
    for name, imd in ours.items():
        bank = Bank.browse(imd.res_id).exists()
        if not bank:
            continue
        vals = banks.get(name)
        if vals is None:
            if bank.active and SHIPPED_XMLID.match(name):
                bank.active = False
                archived.append(name)
            continue
        want = {
            "name": vals["name"],
            "code": vals["code"],
            "country": countries[vals["country_code"]].id,
            "active": True,
        }
        if vals["bic"]:
            want["bic"] = vals["bic"]
        diff = {
            key: value for key, value in want.items()
            if (bank[key].id if key == "country" else bank[key]) != value
        }
        if diff:
            bank.write(diff)
            changed.append(name)
    _logger.info("%s: registry sync updated %d bank(s), archived %d (%s)",
                 MODULE, len(changed), len(archived), ", ".join(archived) or "-")
    return changed, archived


def pre_init_hook(env):
    adopt_existing_banks(env)


def post_init_hook(env):
    sync_registry(env)
