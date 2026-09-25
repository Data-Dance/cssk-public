from odoo import _

# Proper Czech names of the regional financial offices (finanční úřady), keyed by
# c_ufo. The official ``l10n_cz.tax_office`` codelist is the source of the *codes*
# (its ``code`` column == c_ufo), but it only carries English territorial-workplace
# names, so the display name is curated here. Code 13 (Specializovaný finanční
# úřad) is a real office that is not enumerated in the official codelist.
_CZ_UFO_NAMES = {
    13: "Specializovaný finanční úřad",
    451: "Finanční úřad pro hlavní město Prahu",
    452: "Finanční úřad pro Středočeský kraj",
    453: "Finanční úřad pro Jihočeský kraj",
    454: "Finanční úřad pro Plzeňský kraj",
    455: "Finanční úřad pro Karlovarský kraj",
    456: "Finanční úřad pro Ústecký kraj",
    457: "Finanční úřad pro Liberecký kraj",
    458: "Finanční úřad pro Královéhradecký kraj",
    459: "Finanční úřad pro Pardubický kraj",
    460: "Finanční úřad pro Kraj Vysočina",
    461: "Finanční úřad pro Jihomoravský kraj",
    462: "Finanční úřad pro Olomoucký kraj",
    463: "Finanční úřad pro Moravskoslezský kraj",
    464: "Finanční úřad pro Zlínský kraj",
}

# Seat (sídlo) of each regional office: (street, zip, city). Source: Finanční
# správa ČR / published registers. Phone is the central FS infoline.
_CZ_UFO_ADDR = {
    13: ("nábřeží Kpt. Jaroše 1000/7", "170 00", "Praha 7"),
    451: ("Štěpánská 619/28", "111 21", "Praha 1"),
    452: ("Na Pankráci 1685/17", "140 21", "Praha 4"),
    453: ("Mánesova 1803/3a", "371 87", "České Budějovice"),
    454: ("Hálkova 14", "305 72", "Plzeň"),
    455: ("Krymská 2a", "360 01", "Karlovy Vary"),
    456: ("Velká Hradební 61", "400 21", "Ústí nad Labem"),
    457: ("1. máje 97", "460 02", "Liberec"),
    458: ("Horova 17", "500 02", "Hradec Králové"),
    459: ("Boženy Němcové 2625", "530 02", "Pardubice"),
    460: ("Tolstého 2", "586 01", "Jihlava"),
    461: ("Náměstí Svobody 4", "602 00", "Brno"),
    462: ("Lazecká 545/22", "779 11", "Olomouc"),
    463: ("Na Jízdárně 3162/3", "709 00", "Ostrava"),
    464: ("Třída Tomáše Bati 21", "761 86", "Zlín"),
}
_CZ_FS_PHONE = "225 092 392"


def _seed_cz_tax_authorities(env):
    """Seed ``cssk.tax.authority`` for CZ from the official ``l10n_cz.tax_office``.

    The set of valid c_ufo codes is taken from ``l10n_cz.tax_office`` (single
    source of truth — stays correct if Odoo updates it), plus the Specializovaný
    finanční úřad (13). Idempotent: matches existing offices by ``submission_code``
    so re-running (or an upgrade) neither duplicates nor clobbers user edits.
    """
    Office = env["cssk.tax.authority"]
    cz = env["res.country"].search([("code", "=", "CZ")], limit=1)
    codes = set(env["l10n_cz.tax_office"].search([]).mapped("code"))
    codes.add(13)  # Specializovaný FÚ — not enumerated in the official codelist
    for code in sorted(codes):
        sub = str(code)
        if Office.with_context(active_test=False).search_count(
            [("country_code", "=", "CZ"), ("submission_code", "=", sub)]
        ):
            continue
        vals = {
            "code": "CZ-%s" % code,
            "submission_code": sub,
            "name": _CZ_UFO_NAMES.get(code, _("Finanční úřad %s") % code),
            "country_id": cz.id,
            "phone": _CZ_FS_PHONE,
        }
        addr = _CZ_UFO_ADDR.get(code)
        if addr:
            vals.update(street=addr[0], zip=addr[1], city=addr[2])
        Office.create(vals)

    # Territorial workplaces (územní pracoviště) as children of the regional
    # offices — for completeness. Their workplace_code is the (optional)
    # c_pracufo. Seeded from the official l10n_cz.tax_office (Czech names).
    regionals = {
        a.submission_code: a
        for a in Office.with_context(active_test=False).search(
            [("country_code", "=", "CZ"), ("parent_authority_id", "=", False)]
        )
    }
    existing_wp = set(
        Office.with_context(active_test=False).search(
            [("country_code", "=", "CZ"), ("parent_authority_id", "!=", False)]
        ).mapped("submission_code")
    )
    # Read the office names in Czech when the language is loaded; on a DB
    # without cs_CZ (fresh installs default to en_US) fall back to the default
    # lang — with_context(lang=<inactive code>) raises "Invalid language code".
    cs_active = env["res.lang"].search([("code", "=", "cs_CZ")], limit=1)
    office_lang = "cs_CZ" if cs_active else None
    for office in env["l10n_cz.tax_office"].with_context(lang=office_lang).search([]):
        wp = str(office.workplace_code)
        parent = regionals.get(str(office.code))
        if not parent or wp in existing_wp:
            continue
        Office.create({
            "code": "CZ-UZP-%s" % office.workplace_code,
            "submission_code": wp,
            "name": office.name or (_("Územní pracoviště %s") % wp),
            "country_id": cz.id,
            "parent_authority_id": parent.id,
        })
