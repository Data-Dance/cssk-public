Known limitations and deliberate simplifications, all of which the allocator
documents inline:

* **Czech rate vintages.** Only the 2026 figures are shipped. The 1 January
  2026 reform changed the *shape* of the formula (85 % of a three-component
  sum instead of 3/4 of a two-component one, limit 1.9× instead of 1.5×), so
  pre-2026 periods cannot be expressed in these fields. Add a rate record if
  you need to recompute an older period.

* **Slovak mixed-class waterfall.** Because each Slovak claim class carries
  its own protected base, the thirds are not a single pot. The allocator
  computes them per class and then applies the Czech-style waterfall, held in
  check by two conservative invariants: no claim may exceed what its own
  class could legally reach on its own, and the employee always retains at
  least the smallest protected base among the claims actually deducted. Where
  the statute is silent on how classes with different bases share the first
  third, this errs towards deducting less. When either invariant trims a
  claim, the freed money is deliberately **not** redistributed to other claims
  that could legally absorb it — the hard constraint is never to exceed a
  legal limit, not to maximise creditor recovery.

* **Slovak cent rounding.** ``NV 268/2006 § 4`` rounds the protected sums to
  eurocents; published tables occasionally differ from the computed value by
  one cent depending on whether an intermediate step is rounded. The
  coefficients are data, so a site that must match a particular published
  table exactly can adjust them.

* **Insolvency.** ``insolvency`` is offered as an order type and is computed
  exactly like a priority execution, which matches the ordinary *oddlužení
  plněním splátkového kalendáře* case. The special regimes (lower deductions
  approved by the court, ``§ 398`` IZ variants) are not modelled.

* **Non-wage income.** Only wages are covered. Deductions from sickness
  benefits, pensions or other income paid by third parties are outside the
  employer's payroll and outside this module.

* **Order of statutory deductions.** The allocator starts from the net wage
  the payroll engine hands it. Ensuring that tax and insurance are withheld
  before garnishments is the payroll structure's job, not this module's.
