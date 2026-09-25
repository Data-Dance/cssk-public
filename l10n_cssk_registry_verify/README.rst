==================================
CZ/SK Company Registry Verification
==================================

``l10n_cssk_core`` answers *is this IČO well-formed?* This module answers
*does the company exist, and is it still alive?* — the step between a
valid-looking number and a decision that costs money.

Usage
=====

.. code-block:: python

    result = env["res.partner"]._cssk_verify_registry("54093431", "SK")
    result["outcome"]   # 'verified'
    result["name"]      # 'Data Dance s.r.o.'
    result["active"]    # True — not dissolved

``outcome`` is one of ``invalid`` (fails the checksum; the register is never
asked), ``unsupported`` (no provider for that country), ``absent`` (the
register holds no such subject), ``verified``, or ``unavailable`` (we could
not ask).

Do not collapse ``absent`` and ``unavailable``
==============================================

They are the reason this module exists. Treating "we could not reach the
register" as "this company does not exist" turns an outage into a wall of
rejected customers; treating it as "verified" opens the gate every time the
register hiccups. Neither default is safe for every caller, so the module
reports and the caller decides — checkout fails open, provisioning fails
closed.

Credits
=======

Slovak data comes from ORSF (https://orsf.sk), which aggregates RPO, ORSR,
ŽRSR, RÚZ and the Finančná správa VAT-payer list under **CC-BY 4.0**.
