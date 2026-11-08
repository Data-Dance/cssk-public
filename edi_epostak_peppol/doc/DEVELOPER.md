# edi_epostak_peppol: developer notes

Not user documentation: this file is not rendered into a page.

## Design

For the Slovak jurisdiction the mandated format is *plain* Peppol BIS 3 /
UBL 2.1 / EN 16931 — there is no national billing CIUS. Transport and document
standard stay cleanly separated:

`account.move._peppol_provider()` is single-valued, so with more than one
Peppol transport installed (ePošťák alongside `edi_editel_peppol`, say) the
choice must be explicit: set **Peppol Transport** in *Settings ▸ EDI ▸
Peppol BIS3* (the field lives in `edi_base_peppol`). Left empty, nothing
goes through Peppol until it is set. Dispatch itself routes on the provider stamped on each message,
so documents already prepared under the previous transport still leave through
it.
