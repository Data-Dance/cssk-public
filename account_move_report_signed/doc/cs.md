---
title: Záporné částky na dobropisech (PDF)
summary: Vytiskne částky na dobropisu odběrateli jako záporná čísla, jak dobropis očekávají čeští a slovenští čtenáři.
verified: 19.0.1.0.1
---

## K čemu slouží {#purpose}

Odoo tiskne dobropis (opravný daňový doklad snižující základ) odběrateli s
kladnými částkami a to, že jde o opačný pohyb, vyjadřuje jen nadpis. Čeští a
slovenští účetní i odběratelé očekávají, že dobropis ukáže snížení
**zápornými** částkami. Modul tištěný doklad podle toho upraví. V účetnictví
nemění nic.

## Co se na PDF změní {#usage}

Na **dobropisu odběrateli** se se znaménkem minus vytisknou:

- jednotková cena a mezisoučet (nebo celková částka, jsou-li ceny s daní)
  každého řádku;
- mezisoučet každého oddílu;
- seskupené řádky dokladu;
- blok součtů: základ daně, daň podle skupin daní a celková částka, u
  dobropisu v cizí měně i v měně společnosti.

Faktury odběratelům, přijaté faktury a **dobropisy od dodavatelů** si
znaménka ponechají. Částka k úhradě, seznam úhrad a platební QR kód se
nemění. Nic se nenastavuje: modul nainstalujte a tiskněte.

## Omezení {#limitations}

- Týká se jen dobropisů odběratelům; dobropisy od dodavatelů vytištěné z
  Odoo zůstávají kladné.
- Zápornou jednotkovou cenu zvolil modul jako způsob zobrazení: množství
  zůstává kladné.
