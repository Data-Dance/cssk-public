from . import models, wizard


def _force_saleorder_report_filename(env):
    """print_report_name is a translated field and core sale ships translated
    expressions ("Objednávka - %s" …) — writing the en_US source in XML
    leaves those stale per-language expressions in place, so force the
    method-call expression for every installed language."""
    report = env.ref("sale.action_report_saleorder", raise_if_not_found=False)
    if not report:
        return
    expression = "object._get_saleorder_report_filename()"
    for lang_code, _name in env["res.lang"].get_installed():
        report.with_context(lang=lang_code).print_report_name = expression


def post_init_hook(env):
    _force_saleorder_report_filename(env)
    journal = env.ref(
        "sale_order_advance_invoice.advance_invoice_journal",
        raise_if_not_found=False,
    )
    if not journal:
        return
    companies = env["res.company"].search([("advance_invoice_journal_id", "=", False)])
    for company in companies:
        if journal.company_id == company:
            company.advance_invoice_journal_id = journal

