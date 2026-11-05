=========
Changelog
=========

All notable changes to **mis_builder_column_breakdown** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.1.1] — 2026-11-05
-------------------------

Fixed
~~~~~

- Slovak and Czech catalogues: translated the strings that were still English.

[19.0.1.1.0] — 2026-11-02
-------------------------

Added
~~~~~

- Notes on breakdown columns: a note carries the breakdown value it belongs
  to, so notes on a value column and on the total of the same period stay
  apart (both show, each on its own cell). Replaces the refusal of 1.0.0.

[19.0.1.0.0] — 2026-11-02
-------------------------

Added
~~~~~

- *Columns by* on a MIS report period: one column per value of a move-line
  field found in the data, then the total; drill-down follows the value;
  sum/comparison columns keep working; notes refused on value columns.
