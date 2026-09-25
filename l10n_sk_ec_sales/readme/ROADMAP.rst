Dodatočný / opravný súhrnný výkaz — what is and is not done
===========================================================

**Done.** The version ships all three ``druhSV`` types (``rdp`` / ``odp`` /
``ddp`` → R / O / D) and the template emits the header flag correctly:
``<riadny>`` / ``<opravny>`` / ``<dodatocny>`` carries ``1`` for the selected
type. The amendment itself comes from the shared statutory mixin —
*Vytvoriť dodatočné podanie* copies the statement, links it back through
``original_return_id``, notes both sides in the chatter, and leaves it in
draft to recompute. So a dodatočný SV can be raised, computed, exported and
filed today.

**Not done — and the first question is whether it should be.** Unlike the
kontrolný výkaz, this module has no correction semantics: no kód opravy, no
storno rows, no delta against the original. A dodatočný SV therefore files
the **full recomputed list** for the period under ``dodatocny=1``.

That is very probably right, and the schema is the reason to think so:
``svdph20.xsd`` gives a ``zaznam`` (supply record) **no correction marker of
any kind**. The only ``oprava`` element in the file sits on ``zaznamCast2``,
which is the call-off-stock register of § 8a — not a credit-note correction —
and we emit those slots empty because the call-off-stock regime is not
supported. A per-record delta is thus not expressible in this form the way it
is in the KV, where ``kod_opravy`` 1/2 exists precisely for it.

So the work is not "build a delta engine". It is:

1. **Confirm the restatement reading against the poučenie k SV**, not against
   the XSD alone. The absence of a correction field is strong evidence and not
   proof: FS SR could still expect a dodatočný SV to list only the changed
   records, and a structure that cannot mark them would simply leave that
   implicit. Until somebody has read the poučenie on this point, what we do is
   an inference.
2. **Test it end to end.** Nothing in this module's suite exercises an
   amendment at all: no test creates a dodatočný SV, checks that ``druhSV``
   flips, or asserts what its records contain. The KV has
   ``test_dodatocny_delta_kopr`` and ``test_dodatocny_chaining``; the SV has
   nothing, which is why the gap went unnoticed.
3. **Decide what the recompute should do about the original.** A restatement
   recomputes from current bookings, so a correction booked after the original
   was filed is picked up automatically — but nothing warns the accountant
   that the figures now differ from what was submitted, and nothing stops a
   dodatočný being filed identical to its original. The KV drops unchanged
   rows and would file an empty výkaz; the SV would file a duplicate.

If the poučenie turns out to want only the changed records, the machinery to
copy is ``l10n_cssk_kv_kh_base``'s ``_apply_dodatocny_delta``, and the trap to
copy with it is ``kv_full_state_json``: a dodatočný built on a previous
dodatočný must diff against the cumulative full state, not against its
predecessor's stored delta.

Also unimplemented, and unrelated to amendments: the § 8a call-off-stock
register (``zaznamCast2``) is always emitted empty.
