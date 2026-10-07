# Ordering templates for ISDOC 6.0.2 invoices.
#
# Each dict mirrors an <xs:sequence> from xsd/isdoc-invoice-6.0.2.xsd: the KEY ORDER
# is the element order the schema mandates. Passed as the `template` argument to
# odoo.addons.account.tools.dict_to_xml, which does `dict.fromkeys(template) | node`
# to enforce that order and (with render_empty_nodes=False) drop any optional node the
# builder left unset.
#
# ISDOC has a single default namespace and no element prefixes, so keys are bare tags.

# -- Parties ---------------------------------------------------------------
Country = {
    'IdentificationCode': {},
    'Name': {},
}
PostalAddress = {
    'StreetName': {},
    'BuildingNumber': {},
    'CityName': {},
    'PostalZone': {},
    'Country': Country,
}
PartyIdentification = {
    'UserID': {},
    'CatalogFirmIdentification': {},
    'ID': {},
}
PartyName = {
    'Name': {},
}
PartyTaxScheme = {
    'CompanyID': {},
    'TaxScheme': {},
}
RegisterIdentification = {
    'RegisterKeptAt': {},
    'RegisterFileRef': {},
    'RegisterDate': {},
    'Preformatted': {},
}
Contact = {
    'Name': {},
    'Telephone': {},
    'ElectronicMail': {},
}
Party = {
    'PartyIdentification': PartyIdentification,
    'PartyName': PartyName,
    'PostalAddress': PostalAddress,
    'PartyTaxScheme': PartyTaxScheme,
    'RegisterIdentification': RegisterIdentification,
    'Contact': Contact,
}
SupplierParty = {'Party': Party}
CustomerParty = {'Party': Party}
Delivery = {'Party': Party}

# -- References ------------------------------------------------------------
OriginalDocumentReferences = {
    'OriginalDocumentReference': {
        'ID': {},
        'IssueDate': {},
        'UUID': {},
    },
}

# -- Invoice lines ---------------------------------------------------------
ClassifiedTaxCategory = {
    'Percent': {},
    'VATCalculationMethod': {},
    'VATApplicable': {},
    'LocalReverseCharge': {},
}
Item = {
    'Description': {},
    'CatalogueItemIdentification': {'ID': {}},
    'SellersItemIdentification': {'ID': {}},
    'SecondarySellersItemIdentification': {'ID': {}},
    'TertiarySellersItemIdentification': {'ID': {}},
    'BuyersItemIdentification': {'ID': {}},
}
InvoiceLine = {
    'ID': {},
    'InvoicedQuantity': {},
    'LineExtensionAmount': {},
    'LineExtensionAmountTaxInclusive': {},
    'LineExtensionTaxAmount': {},
    'UnitPrice': {},
    'UnitPriceTaxInclusive': {},
    'ClassifiedTaxCategory': ClassifiedTaxCategory,
    'Note': {},
    'Item': Item,
}
InvoiceLines = {'InvoiceLine': InvoiceLine}

# -- Deposits (advance payments already invoiced) --------------------------
NonTaxedDeposit = {
    'ID': {},
    'VariableSymbol': {},
    'DepositAmount': {},
}
NonTaxedDeposits = {'NonTaxedDeposit': NonTaxedDeposit}
TaxedDeposit = {
    'ID': {},
    'VariableSymbol': {},
    'TaxableDepositAmount': {},
    'TaxInclusiveDepositAmount': {},
    'ClassifiedTaxCategory': ClassifiedTaxCategory,
}
TaxedDeposits = {'TaxedDeposit': TaxedDeposit}

# -- Tax & monetary totals -------------------------------------------------
TaxCategory = {
    'Percent': {},
    'VATApplicable': {},
}
TaxSubTotal = {
    'TaxableAmount': {},
    'TaxAmount': {},
    'TaxInclusiveAmount': {},
    'AlreadyClaimedTaxableAmount': {},
    'AlreadyClaimedTaxAmount': {},
    'AlreadyClaimedTaxInclusiveAmount': {},
    'DifferenceTaxableAmount': {},
    'DifferenceTaxAmount': {},
    'DifferenceTaxInclusiveAmount': {},
    'TaxCategory': TaxCategory,
}
TaxTotal = {
    'TaxSubTotal': TaxSubTotal,
    'TaxAmount': {},
}
LegalMonetaryTotal = {
    'TaxExclusiveAmount': {},
    'TaxInclusiveAmount': {},
    'AlreadyClaimedTaxExclusiveAmount': {},
    'AlreadyClaimedTaxInclusiveAmount': {},
    'DifferenceTaxExclusiveAmount': {},
    'DifferenceTaxInclusiveAmount': {},
    'PayableRoundingAmount': {},
    'PaidDepositsAmount': {},
    'PayableAmount': {},
}

# -- Payment means ---------------------------------------------------------
# Transfer-payment branch of DetailsType (cash branch = DocumentID + IssueDate).
# Bank fields come from <xs:group ref="BankAccount"/>: ID, BankCode, Name, IBAN, BIC.
Details = {
    'PaymentDueDate': {},
    'ID': {},
    'BankCode': {},
    'Name': {},
    'IBAN': {},
    'BIC': {},
    'VariableSymbol': {},
    'ConstantSymbol': {},
    'SpecificSymbol': {},
}
Payment = {
    'PaidAmount': {},
    'PaymentMeansCode': {},
    'Details': Details,
}
PaymentMeans = {'Payment': Payment}

# -- Root ------------------------------------------------------------------
Invoice = {
    '_tag': 'Invoice',
    'DocumentType': {},
    'ID': {},
    'UUID': {},
    'IssuingSystem': {},
    'IssueDate': {},
    'TaxPointDate': {},
    'VATApplicable': {},
    'ElectronicPossibilityAgreementReference': {},
    'Note': {},
    'LocalCurrencyCode': {},
    'ForeignCurrencyCode': {},
    'CurrRate': {},
    'RefCurrRate': {},
    'AccountingSupplierParty': SupplierParty,
    'AccountingCustomerParty': CustomerParty,
    'OriginalDocumentReferences': OriginalDocumentReferences,
    'Delivery': Delivery,
    'InvoiceLines': InvoiceLines,
    'NonTaxedDeposits': NonTaxedDeposits,
    'TaxedDeposits': TaxedDeposits,
    'TaxTotal': TaxTotal,
    'LegalMonetaryTotal': LegalMonetaryTotal,
    'PaymentMeans': PaymentMeans,
}
