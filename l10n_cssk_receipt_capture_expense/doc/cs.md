---
title: Zpracování účtenek — výdaje zaměstnanců
summary: Ze zachycené účtenky vytvoří jeden výdaj zaměstnance s DPH zaúčtovanou podle sazeb a přečte účtenky nahrané nebo naskenované v aplikaci Výdaje.
verified: 19.0.1.1.0
family: l10n_cssk_receipt_capture#expenses
---

Přidá na zachycenou účtenku tlačítko **Create Expenses** — jeden výdaj za celou účtenku bez ohledu na sazby DPH, přičemž DPH i účetní zápis se sestaví sazbu po sazbě z rekapitulace účtenky — a naučí aplikaci Výdaje číst účtenky: každý obrázek, který zaměstnanec nahraje, se stane zachycenou účtenkou, a přečte-li se bez chyby, vyplní svůj výdaj; v nabídce *Výdaje → Mé výdaje* přibudou **Scan Receipt** a **My Receipts**. Výdaj, který se od účtenky změnil, se odmítne zaúčtovat, a účtenka uplatněná jako výdaj se už nemůže stát nákupní účtenkou.

Potřebuje [module:l10n_cssk_receipt_capture](module:l10n_cssk_receipt_capture) a aplikaci Výdaje (Community). Nastavení *Capture on Expense Upload* (výchozí zapnuto) a *Receipt Expense Category* jsou v *Výdaje → Konfigurace → Nastavení*; s nainstalovaným čtením pomocí AI je každé nahrání placeným čtením.
