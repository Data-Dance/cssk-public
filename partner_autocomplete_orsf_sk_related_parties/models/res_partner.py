# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Fetch the ownership / officer graph for one partner, on demand.

§ 17 ods. 5 zákona o dani z príjmov subjects transactions between *závislé
osoby* to transfer-pricing documentation. Nothing in an Odoo database knows
which partners are related to the company or to each other, so the question is
answered — when it is answered at all — from memory.

ORSF's graph endpoint answers it mechanically. Two constraints shape everything
below:

* **It is gated, and gated for a reason.** ORSF cites GDPR Art. 6(1)(f) and
  says in as many words: *never bulk-fetch persons*. So this is a per-partner
  button. There is no cron, no batch server action and no list-view multi
  select — deliberately, not as an omission to fill in later.
* **The response shape is not in ORSF's OpenAPI spec.** It documents only
  "nodes + edges (graphology-compatible JSON)". The parser below therefore
  accepts the dialects graphology actually emits, and is written so that
  correcting it means editing one method.
"""

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

GRAPH_DEPTH = 2
# Node attributes that have been seen to carry each meaning across graphology
# serialisations. First hit wins.
_NAME_KEYS = ("label", "name", "title")
_ICO_KEYS = ("ico", "nationalId", "national_id", "cin")
_KIND_KEYS = ("kind", "type", "nodeType", "category")
_ROLE_KEYS = ("role", "label", "relation", "type")


class ResPartner(models.Model):
    _inherit = "res.partner"

    orsf_sk_related_party_ids = fields.One2many(
        "orsf.sk.related.party",
        "partner_id",
        string="Related parties",
    )
    orsf_sk_related_party_count = fields.Integer(
        string="Related party count",
        compute="_compute_orsf_sk_related_party_count",
    )
    orsf_sk_related_parties_fetched_at = fields.Datetime(
        string="Related parties fetched", readonly=True, copy=False
    )

    @api.depends("orsf_sk_related_party_ids")
    def _compute_orsf_sk_related_party_count(self):
        for partner in self:
            partner.orsf_sk_related_party_count = len(
                partner.orsf_sk_related_party_ids
            )

    # -- fetching ----------------------------------------------------------

    def action_orsf_sk_fetch_related_parties(self):
        """Refresh this one partner's related parties from ORSF.

        ``ensure_one`` is load-bearing: it is what keeps the button off a
        multi-record list selection, which is exactly the bulk profiling ORSF
        asks callers not to do.
        """
        self.ensure_one()
        provider = self.env.get("partner.autocomplete.provider.orsf_sk")
        if provider is None:
            raise UserError(
                _("The ORSF provider module is not installed.")
            )
        ico = provider._orsf_normalise_ico(
            self.company_registry or self.partner_gid
        )
        if not ico:
            raise UserError(
                _(
                    "%s has no IČO. Fill the Company ID first — the register is "
                    "keyed on it.",
                    self.display_name,
                )
            )
        if not provider._orsf_cookies():
            raise UserError(
                _(
                    "ORSF gates the ownership graph behind a signed-in "
                    "session, and issues no API key for it.\n\n"
                    "Set an ORSF account e-mail and password in Settings ▸ "
                    "Contacts ▸ ORSF; the session is then obtained and "
                    "refreshed automatically.\n\n"
                    "If they are already set, the sign-in was refused — check "
                    "them, and the server log for the reason."
                )
            )

        body = provider._orsf_get(
            f"/companies/{ico}/graph",
            {"depth": GRAPH_DEPTH},
            authenticated=True,
        )
        if body is None:
            raise UserError(
                _(
                    "ORSF returned no graph for IČO %s. The session token may "
                    "have expired, or the rate limit was reached — the server "
                    "log has the detail.",
                    ico,
                )
            )

        rows = self._orsf_sk_parse_graph(body, ico)
        self.orsf_sk_related_party_ids.unlink()
        now = fields.Datetime.now()
        self.env["orsf.sk.related.party"].create(
            [dict(row, partner_id=self.id, fetched_at=now) for row in rows]
        )
        self.orsf_sk_related_parties_fetched_at = now
        self._orsf_sk_link_related_partners()
        return True

    # -- parsing -----------------------------------------------------------

    @api.model
    def _orsf_sk_graph_attr(self, node, keys):
        """Read the first present key, from the node or its `attributes` dict.

        graphology serialises as ``{"key": …, "attributes": {…}}``, but several
        exporters flatten the attributes onto the node. Accept both.
        """
        attributes = node.get("attributes")
        attributes = attributes if isinstance(attributes, dict) else {}
        for key in keys:
            value = node.get(key) or attributes.get(key)
            if value:
                return value
        return None

    @api.model
    def _orsf_sk_parse_graph(self, body, origin_ico):
        """Turn a graphology graph into related-party rows.

        Shape is unverified against live ORSF output — the API's own spec
        documents no schema for it. Everything unrecognised is skipped rather
        than guessed at, so a shape change costs coverage, not correctness.
        """
        nodes = body.get("nodes")
        edges = body.get("edges")
        if not isinstance(nodes, list) or not isinstance(edges, list):
            _logger.warning(
                "ORSF graph for %s is not nodes+edges (%s); nothing parsed.",
                origin_ico,
                sorted(body)[:8],
            )
            return []

        by_key = {}
        for node in nodes:
            if not isinstance(node, dict):
                continue
            key = node.get("key") or node.get("id")
            if key is not None:
                by_key[str(key)] = node

        origin_keys = {
            key
            for key, node in by_key.items()
            if str(self._orsf_sk_graph_attr(node, _ICO_KEYS) or "") == str(origin_ico)
        }

        # Persons adjacent to the origin, and the role each holds there.
        person_roles = {}
        for edge in edges:
            if not isinstance(edge, dict):
                continue
            source, target = str(edge.get("source")), str(edge.get("target"))
            for near, far in ((source, target), (target, source)):
                if near in origin_keys and far in by_key and far not in origin_keys:
                    person_roles.setdefault(
                        far, self._orsf_sk_graph_attr(edge, _ROLE_KEYS)
                    )

        rows = []
        seen = set()
        for person_key, origin_role in person_roles.items():
            person = by_key[person_key]
            person_name = self._orsf_sk_graph_attr(person, _NAME_KEYS)
            person_ico = self._orsf_sk_graph_attr(person, _ICO_KEYS)
            if person_ico and str(person_ico) == str(origin_ico):
                continue

            # Degree 1: the person themselves, as an officer of this partner.
            if person_name and not person_ico:
                key = (None, person_name, origin_role)
                if key not in seen:
                    seen.add(key)
                    rows.append(
                        {
                            "related_name": person_name,
                            "related_ico": False,
                            "link_person": person_name,
                            "link_role": origin_role or False,
                            "degree": 1,
                        }
                    )

            # Degree 2: other companies that person is attached to.
            for edge in edges:
                if not isinstance(edge, dict):
                    continue
                source, target = str(edge.get("source")), str(edge.get("target"))
                if person_key not in (source, target):
                    continue
                other_key = target if source == person_key else source
                if other_key in origin_keys or other_key not in by_key:
                    continue
                other = by_key[other_key]
                other_ico = self._orsf_sk_graph_attr(other, _ICO_KEYS)
                other_name = self._orsf_sk_graph_attr(other, _NAME_KEYS)
                if not other_ico or not other_name:
                    continue
                key = (str(other_ico), other_name, person_name)
                if key in seen:
                    continue
                seen.add(key)
                rows.append(
                    {
                        "related_name": other_name,
                        "related_ico": str(other_ico),
                        "link_person": person_name or False,
                        "link_role": self._orsf_sk_graph_attr(edge, _ROLE_KEYS)
                        or False,
                        "degree": 2,
                    }
                )
        return rows

    def _orsf_sk_link_related_partners(self):
        """Point each row at the contact it names, where we already have one."""
        for partner in self:
            rows = partner.orsf_sk_related_party_ids.filtered(
                lambda r: r.related_ico and not r.related_partner_id
            )
            if not rows:
                continue
            matches = self.env["res.partner"].search(
                [("company_registry", "in", rows.mapped("related_ico"))]
            )
            by_ico = {p.company_registry: p for p in matches}
            for row in rows:
                match = by_ico.get(row.related_ico)
                if match:
                    row.related_partner_id = match.id

    def action_orsf_sk_open_related_parties(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Related parties — %s", self.display_name),
            "res_model": "orsf.sk.related.party",
            "view_mode": "list,form",
            "domain": [("partner_id", "=", self.id)],
            "context": {"default_partner_id": self.id},
        }
