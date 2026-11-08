# edi_epostak_base: developer notes

Not user documentation: this file is not rendered into a page.

## Why the metadata is read out of the UBL

ePošťák wants routing metadata (sender/receiver participant, document type id,
process id) *alongside* the document, and rejects a submission whose metadata
disagrees with the `cbc:EndpointID` inside the payload (error
`SAPI-DOC-025`). So the document is treated as the single source of truth:
`_epostak_parse_ubl` reads the participants from the UBL's own EndpointID
elements — `schemeID` attribute included — and composes the Peppol document
type identifier structurally::

<root-namespace>::<root-element>##<CustomizationID>::<UBLVersionID>

Both UBL party shapes are handled: `cac:AccountingSupplierParty` /
`cac:AccountingCustomerParty` on an invoice, and `cac:SenderParty` /
`cac:ReceiverParty` on an ApplicationResponse — so an Invoice Response we
send as the *buyer* is addressed correctly too.
