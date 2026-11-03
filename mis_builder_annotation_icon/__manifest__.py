# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "MIS Builder Annotation Icon",
    "version": "19.0.1.0.0",
    "summary": "Annotate a MIS Builder cell from a note icon instead of a dropdown "
               "caret that looks like the line could be expanded.",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Reporting",
    "depends": ["mis_builder"],
    "assets": {
        "web.assets_backend": [
            "mis_builder_annotation_icon/static/src/annotation_icon.xml",
            "mis_builder_annotation_icon/static/src/annotation_icon.scss",
        ],
    },
    "installable": True,
    "auto_install": True,
}
