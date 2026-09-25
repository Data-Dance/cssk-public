"""Force the sale-order report filename expression for every installed
language — print_report_name is a translated field, and core sale ships
per-language expressions ("Objednávka - %s" …) that would otherwise keep
naming advance-invoice PDFs "Order"."""

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    report = env.ref("sale.action_report_saleorder", raise_if_not_found=False)
    if not report:
        return
    expression = "object._get_saleorder_report_filename()"
    for lang_code, _name in env["res.lang"].get_installed():
        report.with_context(lang=lang_code).print_report_name = expression
