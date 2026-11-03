---
title: MIS Builder Annotation Icon
summary: Annotate a MIS Builder report cell from a note icon instead of a dropdown caret that looked like the row could be expanded.
verified: 19.0.1.0.0
---

## What it is for {#purpose}

[module:mis_builder](module:mis_builder) lets you attach a note to a report
cell. It offered this through a dropdown caret in every cell, opening a menu
with a single item, *Annotate*. A downward caret reads as "this row can be
expanded", which is confusing next to rows that really do unfold, and cells
that cannot be annotated showed a greyed caret as well.

This module replaces the caret with a note icon. There is nothing to set up:
it installs with `mis_builder` and changes nothing else.

## How it behaves {#behaviour}

- Point at a row and an empty note icon appears next to each value that can
  be annotated; click it to write the note. The dialog is the same as before.
- A cell that has a note shows a filled icon all the time, next to the
  footnote number. Click it to change the note; the note itself is listed
  under the report, where it can also be deleted.
- Cells that cannot be annotated (such as detail rows) show no icon.
- Only users allowed to edit annotations see the icon at all.
