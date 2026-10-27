* The salary rules, statutory figures, time-off types and the annual tax
  reconciliation stay in the engine modules: they are built on each engine's
  own models (``hr.rule.parameter``, work entry types or payroll codes,
  payslip input types), so they are not shareable as they stand.
* The annual tax reconciliation model is largely the same code on both
  engines; moving it here behind engine accessors is possible but would move
  a whole model with its table, and was left for a later step.
