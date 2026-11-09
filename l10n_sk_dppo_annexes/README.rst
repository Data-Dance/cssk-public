SK DPPO itemised Table A
===========================

Evidenced non-deductible expense items feed the selected return version's
native Table A input rows. Native return lines calculate the totals and r130.
Table B and r150/r250 keep the native depreciation-register source.

Requires l10n_sk_dppo 19.0.1.5.0 and l10n_cssk_income_tax_base 19.0.1.6.0.
Enable the workpaper, enter expense rows, amounts and evidence, review it and
compute the return. Amendments copy the items but require independent review.
Removing items or disabling the workpaper releases generated overrides on
recompute while retaining unrelated manual rows.

Native filing history retains exported XML. This module does not replace
attachments, download streams, the Table B template or the tax calculation.

See doc/en.md and doc/sk.md for workflow and scope. Documentation-generator
validation is not available in the generated public repository.