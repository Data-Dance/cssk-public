=========
Changelog
=========

[Unreleased]
============

Added
~~~~~

* Reviewed HR-event registration601 declarations, independent of payroll engines.
* Published XML and Latin2 text interfaces with pinned PDF-derived XSD provenance.
* Common declaration/archive workflow, explicit corrections, source/calendar checks,
  dated optional payroll eligibility, HR/company access and protected filed history.

Fixed
~~~~~

* Child-event changes advance the batch version so a stale generation/filing
  transaction retries. Covered with two real transactions on a committed batch.

* Retain the company, insurer, period, serial and correction identity after a filed
  batch is reset, including when its working event rows are cleared. An unchanged
  native date write remains idempotent. The original archive cannot be reassigned.
