===========================
MIS Builder Annotation Icon
===========================

MIS Builder offers to annotate a report cell through a dropdown caret in every
cell, opening a menu with a single item, *Annotate*. A downward caret reads as
"this line can be expanded", and cells that cannot be annotated show a greyed
caret as well.

This module replaces it with a note icon:

* it opens the annotation dialog directly;
* it appears on the row under the pointer (and on keyboard focus);
* it stays visible, filled, when the cell already has a note;
* it is absent on cells that cannot be annotated.

It installs automatically with ``mis_builder`` and changes nothing else.
