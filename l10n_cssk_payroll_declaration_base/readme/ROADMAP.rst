Engine neutrality
-----------------

The point of this module is that a declaration can be built from either
payroll engine. ``_collect_payslip_totals`` reads only the ``hr.payslip`` API
that the OCA ``payroll`` engine and Enterprise ``hr_payroll`` genuinely share,
so the module depends on neither.

That neutrality is currently a design property, not a tested one. Each
dependent module's test suite drives whichever engine happens to be installed
in the database and asserts against that one; nothing asserts that the two
engines produce IDENTICAL declarations from identical inputs. Until a
cross-engine parity test exists, a divergence introduced in one country
module's rules would surface as a wrong declaration rather than as a failing
test. This is the single most valuable test to add to the family.

Not covered
-----------

* The state machine is ``draft → generated → submitted``. Submission is
  recorded, not performed: no module in the family talks to an authority
  portal, so "submitted" means a human filed it and marked it so.
* There is no correction/annulment concept. Every form in the family has one
  (opravný / dodatočný / storno), and none of them set the markers — a
  correction has to be filed through the portal by hand.
* Form vintages are additive. A new ``cssk.payroll.declaration.version`` brings
  its own QWeb template and XSD; superseded vintages are kept but not
  back-filled, so recomputing an old period requires the vintage that was in
  force at the time.
* XSD validation checks the shape of the XML, never the correctness of the
  figures. Reconcile the first live filing of any form by hand.

Corrections — remaining forms
=============================

Three forms are wired to ``correction_type``: the SK Prehľad (riadny/opravný),
the SK Hlásenie (rh/oh/dh) and the CZ PPPZ (typPrehledu). The other nine are
declared regular-only until each is checked against its own authority's rules.
What the shipped XSDs say so far:

* **CZ PVPOJ** — carries a ``corrIDStorna`` attribute, "Odkaz na záznam, který
  je stornován - pouze pro storno". Note this is a per-RECORD storno referring
  to an individual employee entry, not a per-filing type the way the wired
  three are, so it needs a different shape from the current mixin field.
* **SK VPP** — has a ``CisloVykazuType``; SP corrections are believed to work
  through the výkaz number rather than a type flag.
* **SK MVP, ELDP, RLFO, dávka 514 and CZ ELDP, ONZ, Vyúčtování** — no type
  element in the template and nothing obvious in the XSD. RLFO in particular
  models corrections as different EVENT types (``ZM`` zmena, ``ZP`` zrušenie
  prihlásenia), which is a different mechanism again.

None of this should be guessed from the shape of the XSD alone — each needs the
authority's own methodology, which is why they stay regular-only rather than
being wired on a plausible reading.
