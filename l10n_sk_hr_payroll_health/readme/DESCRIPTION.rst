Monthly Slovak **dávka 514** (Mesačný výkaz preddavkov na poistné) — the
health-insurance advances statement filed each month to the target health
insurance company (VšZP 25, Dôvera 24, Union 27) through its e-pobočka.

The dávka 514 record set is defined centrally by the ÚDZS/MZSR and is identical
across all three insurers, so one writer is parameterised by the insurer code
(``kód ZP``) and the payer/bank details. The exported XML (root ``MZSR``)
follows the official ``514-2023.xsd`` element model exactly: an
``Identification`` block, a ``CorporateBody`` block, an ``InsuranceBody``
employer aggregate and one ``PersonData`` row per employee (rodné číslo,
vymeriavací základ, employer / employee advance, počet dní).

Rule-code mapping (rates come from the payslip, not hardcoded):
``DepositOfEmployer`` ← ``HEALTHEMPLOYER``, ``DepositOfEmployee`` ←
``HEALTH``, ``DepositOffEmployeeAdd`` (minimum-advance top-up) ←
``HEALTHDOPLATOK`` / ``HEALTH_DOPLATOK``.

**Schema caveat.** The official ``514-2023.xsd`` is shipped in ``data/`` and is
loaded into the export pipeline, but the published schema is internally
defective — its ID/string fields carry a single-character ``[0-9]`` pattern
under an 8-12 char ``minLength``, its day / birth-number integer fields carry
impossible ``maxInclusive`` bounds (2 / 10), and ``DateOfSending`` mixes an
``xs:date`` base with a YYYYMMDD-only pattern — so **no real-world instance can
pass ``assertValid``**. The pipeline therefore runs the XSD as a *non-fatal*
check (violations are logged) and gates on well-formedness + structural
conformance to the schema's element model (root + the three blocks +
``NumberOfRecords`` = row count + key totals). Element names/order match the
official schema; reconcile the figures with the insurer before live filing.

Engine-neutral: it reads payslips through the shared
``l10n_cssk_payroll_declaration_base`` adapter and works on both the
``payroll`` engine and the ``hr_payroll`` engine.
