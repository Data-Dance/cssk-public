# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.tools import file_open
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory


@tagged("post_install", "-at_install")
class TestDppoPaperInputCapacity(TransactionCase):
    def test_keep_full_input_for_exact_statutory_validation(self):
        # Char(size=N) silently truncates before a later format validation.
        # Preserve the supplied data so the form adapter can reject it.
        ret = self.env["cssk.income.tax.return"].new({
            "l10n_sk_form_legal_code": "1129", "l10n_sk_form_nace": "620109"})
        self.assertEqual(ret.l10n_sk_form_legal_code, "1129")
        self.assertEqual(ret.l10n_sk_form_nace, "620109")

    def test_equal_snapshot_bytes_across_python_hash_seeds(self):
        paths = []
        for name in ("models/official_pdf.py", "static/forms/DPPOv26.pdf",
                     "static/forms/DPPOv26-layout.json"):
            with file_open("l10n_sk_dppo/" + name, "rb") as source:
                paths.append(source.name)
        data = {"header": {"dic": "2020317068", "ico": "36000001", "name": "Synthetic",
                           "legal_code": "112", "nace": "62010"}, "flags": {}, "rows": {"r100": 0},
                "date_from": "2027-01-01", "date_to": "2027-12-31",
                "prepared_on": "2028-03-01", "statement_type": "R"}
        script = ("import json,runpy,sys; from pathlib import Path; "
                  "module=runpy.run_path(sys.argv[1]); "
                  "sys.stdout.buffer.write(module['render_official_form']("
                  "Path(sys.argv[2]).read_bytes(),json.loads(Path(sys.argv[3]).read_text()),"
                  "json.loads(Path(sys.argv[4]).read_text())))")
        with TemporaryDirectory() as directory:
            payload = Path(directory) / "input.json"
            payload.write_text(json.dumps(data), encoding="utf-8")
            results = [subprocess.check_output([sys.executable, "-c", script, *paths, str(payload)],
                       env={**os.environ, "PYTHONHASHSEED": str(seed)}, timeout=45)
                       for seed in (1, 2)]
        self.assertEqual(results[0], results[1])
