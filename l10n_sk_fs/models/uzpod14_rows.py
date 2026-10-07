# -*- coding: utf-8 -*-
"""UZPODv14 row -> account mapping, flattened from the official SK uctovna
zavierka structure (mirrors the authoritative statutory definitions).
Each cell is ``(acct_formula, conds)``: acct_formula = signed comma-separated
account-code prefixes; conds = ``[low, high, mode, sign]`` conditional terms
(net of accounts in ``[low, high)`` contributed x sign only when net is
positive (pos) / negative (neg)) — the sum_if_pos / sum_if_neg tax-account
receivable/payable split. NOTE: a few financial income/cost subdivisions
(IX/X/XI, N) select accounts by tax TAG in EE and are not mapped here (gap).
AKTIVA r001-r078: (gross_acct, gross_conds, adj_acct, adj_conds).
PASIVA r079-r145 and VZS r01-r61: (net_acct, net_conds)."""


class _SUM(tuple):
    """A total row, written as the rows it adds up rather than as accounts.

    The totals used to carry their own account lists, and those drifted from
    their leaves in both directions: 098000 and 481000 were named by a leaf
    and by no total, 255100 and 473100 by the totals and by no leaf, and
    221100 by two sibling leaves so r001 counted it twice. A total that IS the
    sum of its leaves cannot disagree with them. Resolved into an ordinary
    ``(formula, conds, ...)`` tuple at import by ``_roll_up``, so every reader
    of these tables still sees accounts.
    """

    def __new__(cls, *codes):
        return super().__new__(cls, codes)


SUVAHA_AKTIVA = [  # r001..r078: (gross_acct, gross_conds, adj_acct, adj_conds)
    _SUM('s002', 's033', 's074'),  # sk_bs_total_assets
    _SUM('s003', 's011', 's021'),  # sk_bs_A
    _SUM('s004', 's005', 's006', 's007', 's008', 's009', 's010'),  # sk_bs_A_I
    ('012000', [], '-072000,-091100', []),  # sk_bs_A_I_1
    ('013000', [], '-073000,-091200', []),  # sk_bs_A_I_2
    ('014000', [], '-074000,-091300', []),  # sk_bs_A_I_3
    ('015000', [], '-075000,-091400', []),  # sk_bs_A_I_4
    ('019000', [], '-079000,-091500,-091000', []),  # sk_bs_A_I_5
    ('041000', [], '-093000', []),  # sk_bs_A_I_6
    ('051000', [], '-095100', []),  # sk_bs_A_I_7
    _SUM('s012', 's013', 's014', 's015', 's016', 's017', 's018', 's019', 's020'),  # sk_bs_A_II
    ('031000', [], '-092300', []),  # sk_bs_A_II_1
    ('021000', [], '-081000,-092100', []),  # sk_bs_A_II_2
    ('022000', [], '-082000,-092200', []),  # sk_bs_A_II_3
    ('025000', [], '-085000,-092500', []),  # sk_bs_A_II_4
    ('026000', [], '-086000,-092600', []),  # sk_bs_A_II_5
    ('029000,032000', [], '-089000,-092320,-092900,-092000', []),  # sk_bs_A_II_6
    ('042000', [], '-094000', []),  # sk_bs_A_II_7
    ('052000', [], '-095200,-095000', []),  # sk_bs_A_II_8
    ('097000', [], '-098000', []),  # sk_bs_A_II_9
    _SUM('s022', 's023', 's024', 's025', 's026', 's027', 's028', 's029', 's030', 's031', 's032'),  # sk_bs_A_III
    ('061000', [], '-096100', []),  # sk_bs_A_III_1
    ('062000', [], '-096200', []),  # sk_bs_A_III_2
    ('063000', [], '-096300', []),  # sk_bs_A_III_3
    ('066100,066000', [], '-096610', []),  # sk_bs_A_III_4
    ('066200', [], '-096620', []),  # sk_bs_A_III_5
    ('067000', [], '-096700', []),  # sk_bs_A_III_6
    ('065000,069000', [], '-096500,-096900,-096000', []),  # sk_bs_A_III_7
    ('068000', [], '-096800', []),  # sk_bs_A_III_8
    ('221100', [], '', []),  # sk_bs_A_III_9
    ('043000', [], '-096043', []),  # sk_bs_A_III_10
    ('053000,055000', [], '-095300', []),  # sk_bs_A_III_11
    _SUM('s034', 's041', 's053', 's066', 's071'),  # sk_bs_B
    _SUM('s035', 's036', 's037', 's038', 's039', 's040'),  # sk_bs_B_I
    ('112000,119000,111000', [], '-191000', []),  # sk_bs_B_I_1
    ('121000,122000', [], '-192000,-193000', []),  # sk_bs_B_I_2
    ('123000', [], '-194000', []),  # sk_bs_B_I_3
    ('124000', [], '-195000', []),  # sk_bs_B_I_4
    ('132000,133000,139000,131000', [], '-196000', []),  # sk_bs_B_I_5
    ('314100', [], '-391341', []),  # sk_bs_B_I_6
    _SUM('s042', 's046', 's047', 's048', 's049', 's050', 's051', 's052'),  # sk_bs_B_II
    _SUM('s043', 's044', 's045'),  # sk_bs_B_II_1
    ('311110', [], '-391110', []),  # sk_bs_B_II_1_a
    ('311120', [], '-391120', []),  # sk_bs_B_II_1_b
    ('311100', [], '-391100', []),  # sk_bs_B_II_1_c
    ('316100', [], '', []),  # sk_bs_B_II_2
    ('351100', [], '-391510', []),  # sk_bs_B_II_3
    ('351200', [], '-391520', []),  # sk_bs_B_II_4
    ('355100', [], '-391550', []),  # sk_bs_B_II_5
    ('373100', [], '-391730', []),  # sk_bs_B_II_6
    ('374000,378100', [], '-391700', []),  # sk_bs_B_II_7
    ('481000', [], '', []),  # sk_bs_B_II_8
    _SUM('s054', 's058', 's059', 's060', 's061', 's062', 's063', 's064', 's065'),  # sk_bs_B_III
    _SUM('s055', 's056', 's057'),  # sk_bs_B_III_1
    ('311200', [], '-391200', []),  # sk_bs_B_III_1_a
    ('311300', [], '-391300', []),  # sk_bs_B_III_1_b
    ('311000,312000,313000,314000,315000', [], '-391000', []),  # sk_bs_B_III_1_c
    ('316000', [], '-391600', []),  # sk_bs_B_III_2
    ('351300,351000', [], '-391530', []),  # sk_bs_B_III_3
    ('351400', [], '-391540', []),  # sk_bs_B_III_4
    ('355000,398000,354000,358000,398100', [], '-391500', []),  # sk_bs_B_III_5
    ('336000', [], '-391336', []),  # sk_bs_B_III_6
    ('', [['341', '342', 'pos_each', 1], ['342', '343', 'pos_each', 1], ['343', '344', 'pos_each', 1], ['345', '346', 'pos_each', 1], ['346', '347', 'pos_each', 1], ['347', '348', 'pos_each', 1]], '-391340', []),  # sk_bs_B_III_7
    ('373000,376000', [], '', []),  # sk_bs_B_III_8
    ('335000,378000,371000,375000', [], '-391800', []),  # sk_bs_B_III_9
    _SUM('s067', 's068', 's069', 's070'),  # sk_bs_B_IV
    ('251100,253100', [], '-291100', []),  # sk_bs_B_IV_1
    ('251000,253000,256000,257000', [], '-291000', []),  # sk_bs_B_IV_2
    ('252000', [], '', []),  # sk_bs_B_IV_3
    ('259000,314200', [], '-291200', []),  # sk_bs_B_IV_4
    _SUM('s072', 's073'),  # sk_bs_B_V
    ('211000,213000', [], '', []),  # sk_bs_B_V_1
    ('221000,261000', [], '', []),  # sk_bs_B_V_2
    _SUM('s075', 's076', 's077', 's078'),  # sk_bs_C
    ('381100,382100', [], '', []),  # sk_bs_C_1
    ('381000,382000', [], '', []),  # sk_bs_C_2
    ('385100', [], '', []),  # sk_bs_C_3
    ('385000', [], '', []),  # sk_bs_C_4
]

SUVAHA_PASIVA = [  # r079..r145: (net_acct, net_conds)
    _SUM('s080', 's101', 's141'),  # sk_bs_total_equity_liabilities
    _SUM('s081', 's085', 's086', 's087', 's090', 's093', 's097', 's100'),  # sk_bs_2_A
    _SUM('s082', 's083', 's084'),  # sk_bs_2_A_I
    ('-411000,-491000', []),  # sk_bs_2_A_I_1
    ('-419000', []),  # sk_bs_2_A_I_2
    ('-353000', []),  # sk_bs_2_A_I_3
    ('-412000', []),  # sk_bs_2_A_II
    ('-413000', []),  # sk_bs_2_A_III
    _SUM('s088', 's089'),  # sk_bs_2_A_IV
    ('-417000,-418000,-421000,-422000', []),  # sk_bs_2_A_IV_1
    ('-417100,-421100', []),  # sk_bs_2_A_IV_2
    _SUM('s091', 's092'),  # sk_bs_2_A_V
    ('-423000', []),  # sk_bs_2_A_V_1
    ('-427000', []),  # sk_bs_2_A_V_2
    _SUM('s094', 's095', 's096'),  # sk_bs_2_A_VI
    ('-414000', []),  # sk_bs_2_A_VI_1
    ('-415000', []),  # sk_bs_2_A_VI_2
    ('-416000', []),  # sk_bs_2_A_VI_3
    _SUM('s098', 's099'),  # sk_bs_2_A_VII
    ('-428000', []),  # sk_bs_2_A_VII_1
    ('-429000', []),  # sk_bs_2_A_VII_2
    ('-5,-6', []),  # sk_bs_2_A_VIII (the export reads it off the movement)
    _SUM('s102', 's118', 's121', 's122', 's136', 's139', 's140'),  # sk_bs_2_B
    _SUM('s103', 's107', 's108', 's109', 's110', 's111', 's112', 's113', 's114', 's115', 's116', 's117'),  # sk_bs_2_B_I
    _SUM('s104', 's105', 's106'),  # sk_bs_2_B_I_1
    ('-321400,-475300,-476100', []),  # sk_bs_2_B_I_1_a
    ('-321600,-475600,-476200', []),  # sk_bs_2_B_I_1_b
    ('-321200,-475200,-476000', []),  # sk_bs_2_B_I_1_c
    ('-316100', []),  # sk_bs_2_B_I_2
    ('-471100,-471000', []),  # sk_bs_2_B_I_3
    ('-471200', []),  # sk_bs_2_B_I_4
    ('-479000', []),  # sk_bs_2_B_I_5
    ('-475000', []),  # sk_bs_2_B_I_6
    ('-478000', []),  # sk_bs_2_B_I_7
    ('-473100,-255100,-473000', []),  # sk_bs_2_B_I_8
    ('-472000', []),  # sk_bs_2_B_I_9
    ('-372200,-474000', []),  # sk_bs_2_B_I_10
    ('-373200,-373100', []),  # sk_bs_2_B_I_11
    ('-481000', []),  # sk_bs_2_B_I_12
    _SUM('s119', 's120'),  # sk_bs_2_B_II
    ('-451200', []),  # sk_bs_2_B_II_1
    ('-459200', []),  # sk_bs_2_B_II_2
    ('-461100,-461000', []),  # sk_bs_2_B_III
    _SUM('s123', 's127', 's128', 's129', 's130', 's131', 's132', 's133', 's134', 's135'),  # sk_bs_2_B_IV
    _SUM('s124', 's125', 's126'),  # sk_bs_2_B_IV_1
    ('-321300,-322100,-324300', []),  # sk_bs_2_B_IV_1_a
    ('-321500,-322200,-324500', []),  # sk_bs_2_B_IV_1_b
    ('-321000,-322000,-324000,-325000,-326000', []),  # sk_bs_2_B_IV_1_c
    ('-316000', []),  # sk_bs_2_B_IV_2
    ('-361100,-361000', []),  # sk_bs_2_B_IV_3
    ('-361200', []),  # sk_bs_2_B_IV_4
    ('-364000,-365000,-366000,-367000,-368000,-398100,-398000', []),  # sk_bs_2_B_IV_5
    ('-331000,-333000', []),  # sk_bs_2_B_IV_6
    ('-336000', []),  # sk_bs_2_B_IV_7
    ('', [['341', '342', 'neg_each', -1], ['342', '343', 'neg_each', -1], ['343', '344', 'neg_each', -1], ['345', '346', 'neg_each', -1], ['346', '347', 'neg_each', -1], ['347', '348', 'neg_each', -1]]),  # sk_bs_2_B_IV_8
    ('-373000,-377000', []),  # sk_bs_2_B_IV_9
    ('-379000,-474100,-372000', []),  # sk_bs_2_B_IV_10
    _SUM('s137', 's138'),  # sk_bs_2_B_V
    ('-323000,-451000', []),  # sk_bs_2_B_V_1
    ('-459000', []),  # sk_bs_2_B_V_2
    ('-221900,-231000,-232000,-461200', []),  # sk_bs_2_B_VI
    ('-241000,-249000,-255000', []),  # sk_bs_2_B_VII
    _SUM('s142', 's143', 's144', 's145'),  # sk_bs_2_C
    ('-383200', []),  # sk_bs_2_C_1
    ('-383000,-383100', []),  # sk_bs_2_C_2
    ('-384200', []),  # sk_bs_2_C_3
    ('-384000,-384100', []),  # sk_bs_2_C_4
]


def _roll_up():
    """Replace every ``_SUM`` with the concatenation of its children's cells.

    Concatenation is exact: the evaluator sums per token, so a total of the
    leaves' tokens is the sum of the leaves, two-sided gating included."""
    rows = {}
    for i, row in enumerate(SUVAHA_AKTIVA, start=1):
        rows["s%03d" % i] = (SUVAHA_AKTIVA, i - 1)
    for i, row in enumerate(SUVAHA_PASIVA, start=1):
        rows["s%03d" % (78 + i)] = (SUVAHA_PASIVA, i - 1)

    def resolve(code):
        table, pos = rows[code]
        row = table[pos]
        if not isinstance(row, _SUM):
            return row
        cells = [resolve(child) for child in row]
        width = len(cells[0])
        merged = []
        for col in range(width):
            if col % 2:  # conds
                merged.append([c for cell in cells for c in (cell[col] or [])])
            else:
                merged.append(",".join(cell[col] for cell in cells if cell[col]))
        table[pos] = tuple(merged)
        return table[pos]

    for code in rows:
        resolve(code)


_roll_up()


def _two_sided():
    """Accounts the Súvaha names on BOTH sides: a pohľadávka when the balance
    is a debit, a záväzok when it is a credit (316, 336, 373, 398, 481 — the
    form's "A" accounts). The export gates each such account on its own
    balance sign; summed ungated, one balance lands on both sides at once.
    Read off the leaf cells: positive in an AKTÍVA gross, negative in a PASÍVA.
    The 341-347 tax split says the same thing with conds and is not here."""
    debit, credit = set(), set()
    for row in SUVAHA_AKTIVA:
        debit |= {t.strip() for t in row[0].split(",")
                  if t.strip() and not t.strip().startswith("-")}
    for row in SUVAHA_PASIVA:
        credit |= {t.strip()[1:] for t in row[0].split(",")
                   if t.strip().startswith("-")}
    return frozenset(debit & credit)


TWO_SIDED = _two_sided()

VZS = [  # r01..r61: (net_acct, net_conds)
    ('-601,-602,-604,-606,-607', []),  # sk_pl_net_turnover
    ('-601,-602,-604,-606,-607,-61,-62,-641,-642,-644,-645,-646,-648,-655,-657', []),  # sk_pl_total_revenue
    ('-604,-607', []),  # sk_pl_revenue_I
    ('-601', []),  # sk_pl_revenue_II
    ('-602,-606', []),  # sk_pl_revenue_III
    ('-61', []),  # sk_pl_revenue_IV
    ('-62', []),  # sk_pl_revenue_V
    ('-641,-642', []),  # sk_pl_revenue_VI
    ('-644,-645,-646,-648,-655,-657', []),  # sk_pl_revenue_VII
    ('501,502,503,504,505,507,51,521,522,523,524,525,526,527,528,53,541,542,543,544,545,546,547,548,549,551,553,555,557', []),  # sk_pl_total_cost
    ('504,507', []),  # sk_pl_total_cost_A
    ('501,502,503', []),  # sk_pl_total_cost_B
    ('505', []),  # sk_pl_total_cost_C
    ('51', []),  # sk_pl_total_cost_D
    ('521,522,523,524,525,526,527,528', []),  # sk_pl_total_cost_E
    ('521,522', []),  # sk_pl_total_cost_E_1
    ('523', []),  # sk_pl_total_cost_E_2
    ('524,525,526', []),  # sk_pl_total_cost_E_3
    ('527,528', []),  # sk_pl_total_cost_E_4
    ('53', []),  # sk_pl_total_cost_F
    ('551,553', []),  # sk_pl_total_cost_G
    ('551', []),  # sk_pl_total_cost_G_1
    ('553', []),  # sk_pl_total_cost_G_2
    ('541,542', []),  # sk_pl_total_cost_H
    ('547', []),  # sk_pl_total_cost_I
    ('543,544,545,546,548,549,555,557', []),  # sk_pl_total_cost_J
    ('-501,-502,-503,-504,-505,-507,-51,-521,-522,-523,-524,-525,-526,-527,-528,-53,-541,-542,-543,-544,-545,-546,-547,-548,-549,-551,-553,-555,-557,-601,-602,-604,-606,-607,-61,-62,-641,-642,-644,-645,-646,-648,-655,-657', []),  # sk_pl_result
    ('-501,-502,-503,-504,-505,-507,-51,-601,-602,-604,-606,-607,-61,-62', []),  # sk_pl_added_value
    ('-661,-662,-663,-664,-665,-666,-667,-668', []),  # sk_pl_total_income
    ('-661', []),  # sk_pl_total_income_VIII
    ('-665', []),  # sk_pl_total_income_IX (Výnosy z krátkodob. fin. majetku, 665)
    ('-665&IX_1', []),  # sk_pl_total_income_IX_1 (prepojené — accounts tagged IX_1)
    ('-665&IX_2', []),  # sk_pl_total_income_IX_2 (podielová účasť — tagged IX_2)
    ('-665!IX_1!IX_2', []),  # sk_pl_total_income_IX_3 (ostatné — 665 not tagged prepojené/podiel.)
    ('-666', []),  # sk_pl_total_income_X (Výnosy z dlhodob. fin. majetku, 666)
    ('-666&X_1', []),  # sk_pl_total_income_X_1 (prepojené — tagged X_1)
    ('-666&X_2', []),  # sk_pl_total_income_X_2 (podielová účasť — tagged X_2)
    ('-666!X_1!X_2', []),  # sk_pl_total_income_X_3 (ostatné — 666 not tagged)
    ('-662', []),  # sk_pl_total_income_XI (Výnosové úroky, 662)
    ('-662&XI_1', []),  # sk_pl_total_income_XI_1 (prepojené — tagged XI_1)
    ('-662!XI_1', []),  # sk_pl_total_income_XI_2 (ostatné — 662 not tagged prepojené)
    ('-663', []),  # sk_pl_total_income_XII
    ('-664,-667', []),  # sk_pl_total_income_XIII
    ('-668', []),  # sk_pl_total_income_XIV
    ('561,562,563,564,565,566,567,568,569', []),  # sk_pl_total_financial_cost
    ('561', []),  # sk_pl_total_financial_cost_K
    ('566', []),  # sk_pl_total_financial_cost_L
    ('565', []),  # sk_pl_total_financial_cost_M
    ('562', []),  # sk_pl_total_financial_cost_N (Nákladové úroky, 562)
    ('562&N_1', []),  # sk_pl_total_financial_cost_N_1 (prepojené — tagged N_1)
    ('562!N_1', []),  # sk_pl_total_financial_cost_N_2 (ostatné — 562 not tagged prepojené)
    ('563', []),  # sk_pl_total_financial_cost_O
    ('564,567', []),  # sk_pl_total_financial_cost_P
    ('568,569', []),  # sk_pl_total_financial_cost_Q
    ('-561,-562,-563,-564,-565,-566,-567,-568,-569,-661,-662,-663,-664,-665,-666,-667,-668', []),  # sk_pl_result_financial
    ('-501,-502,-503,-504,-505,-507,-51,-521,-522,-523,-524,-525,-526,-527,-528,-53,-541,-542,-543,-544,-545,-546,-547,-548,-549,-551,-553,-555,-557,-561,-562,-563,-564,-565,-566,-567,-568,-569,-601,-602,-604,-606,-607,-61,-62,-641,-642,-644,-645,-646,-648,-655,-657,-661,-662,-663,-664,-665,-666,-667,-668', []),  # sk_pl_before_tax
    ('591,592,595', []),  # sk_pl_income_tax
    ('591,595', []),  # sk_pl_income_tax_1
    ('592', []),  # sk_pl_income_tax_2
    ('596', []),  # sk_pl_transfer
    ('-5,-6', []),  # sk_pl_after_tax — VH po zdanení = výnosy − náklady vrátane
    # dane = −(Σ trieda 5 + Σ trieda 6). Rovná sa Súvaha r100 (A.VIII) z rovnakého
    # pohybu tried 5/6, takže bilancia sedí čestne (bez dopočtu). Predtým sa tento
    # riadok počítal enumeráciou účtov a vynechával 562/662/665/666 → r61 ≠ r56 − daň.
]


def _claimed_analytics():
    """Six-digit analytic codes (NNNxxx, xxx != '000') that some row routes
    explicitly. A synthetic-main token NNN000 then absorbs only the analytics of
    NNN that are NOT explicitly claimed — so analytic sub-accounts (e.g. 022001,
    022002) land on their synthetic's Súvaha line, while genuine per-analytic
    splits stay precise and aren't double-counted."""
    claimed = set()

    def add(f):
        for tok in (f or "").replace("-", "").split(","):
            tok = tok.strip()
            if len(tok) == 6 and not tok.endswith("000"):
                claimed.add(tok)

    for r in SUVAHA_AKTIVA:
        add(r[0])
        add(r[2])
    for r in SUVAHA_PASIVA:
        add(r[0])
    for r in VZS:
        add(r[0])
    return claimed


CLAIMED_ANALYTICS = _claimed_analytics()
