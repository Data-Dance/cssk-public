from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    cssk_vat_deferral_account_id = fields.Many2one(
        "account.account",
        string="VAT declared in a later period",
        check_company=True,
        help="Optional. When a document's VAT is declared in a later period "
        "than it is booked (its 'VAT period declared' date), the tax is moved "
        "to this account on the booking date and back on the declaration "
        "date, so the VAT accounts (343) agree with the return of every "
        "period. Leave empty to keep the tax where it was booked.",
    )
    l10n_cssk_tax_authority_id = fields.Many2one(
        "cssk.tax.authority",
        string="Tax Authority",
        domain="[('country_code', '=', account_fiscal_country_id.code)]",
        help="Tax office this company files its statutory returns to. Used as "
        "the addressee in DPH / KV·KH / FS XML exports.",
    )
    l10n_cssk_person_type_id = fields.Many2one(
        "cssk.person.type",
        string="Entity Type",
        domain="[('country_code', '=', account_fiscal_country_id.code)]",
        help="Legal form of the company (legal entity / natural person), used "
        "by statutory reports.",
    )
    # DIČ lives on the company's partner record — no duplicate storage.
    # § 3a ods. 1 Obchodného zákonníka (SK) and § 435 občanského zákoníku (CZ)
    # require business documents to state the register and the entry number, so
    # this text is printed on invoices rather than merely stored.
    # Translatable: the clause is printed in the language of the document, and a
    # company registered in both countries needs both wordings.
    l10n_cssk_registration_info = fields.Text(
        string="Registration Info",
        translate=True,
        help="Commercial-register entry printed on invoices and other business "
        "documents, e.g. 'Spoločnosť zapísaná v obchodnom registri Mestského "
        "súdu Bratislava III, oddiel: Sro, vložka č. 155723/B.'",
    )
    # Year-end closing and reopening entries (trieda 5/6 -> 710, súvahové účty
    # -> 702, reopened from 701) are an artefact of the ledger, not activity of
    # the period. Left in, they wreck every statutory statement: the balance
    # sheet reads a cumulative as-of balance, so at the year-end date the close
    # has landed but the reopen has not, and every year-end degenerates to the
    # same closed-out state; the P&L reads a movement window, so the 5/6 close
    # cancels the year's revenue and cost.
    #
    # BOTH halves have to go, not just the terminal one. Because the as-of read
    # has no lower date bound, dropping the matched close/reopen pair lets the
    # real transactional history accumulate on its own — no reconstruction. Drop
    # only the closing and every opening balance is counted twice from the
    # second year onwards.
    #
    # Journals rather than a flag on account.move: OCA account_fiscal_year_closing
    # (which l10n_sk_fiscal_year_closing / l10n_cz_fiscal_year_closing extend) already books its closing
    # and opening moves through a configurable journal, so one mechanism covers
    # natively closed companies and ledgers migrated in from another system. It
    # also stays inspectable and fixable by the accountant, and needs no extra
    # stored column on a table that holds every line the company ever posted.
    #
    # Deliberately NOT keyed on accounts 701/702/710: l10n_sk ships those as
    # off_balance and l10n_sk_fiscal_year_closing retypes them (account_move_line.
    # _check_off_balance refuses to mix off-balance accounts with any other in
    # one entry, which makes the classic Czechoslovak close unpostable), so the
    # very codes such a rule would key on are the ones our own modules rewrite.
    # It would also miss closing entries that never touch 710.
    l10n_cssk_closing_journal_ids = fields.Many2many(
        "account.journal",
        "res_company_cssk_closing_journal_rel",
        "company_id",
        "journal_id",
        string="Year-end closing journals",
        domain="[('company_id', '=', id)]",
        help="Journals holding the year-end closing and reopening entries "
        "(e.g. UZAVIERKA and OTVORENIE). Entries in these journals are left "
        "out of the statutory financial statements and the income-tax return, "
        "which report the activity of the period, not the ledger's own "
        "close/reopen mechanics. Leave empty if the year is never closed in "
        "this database.",
    )
