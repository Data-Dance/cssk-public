---
title: Platební režim — úhrada při zaúčtování
summary: Platební režim může zaregistrovat úhradu hned při zaúčtování faktury — u prodeje zaplaceného na místě v hotovosti nebo kartou.
verified: 19.0.1.0.0
---

## K čemu slouží {#purpose}

Zaplatí-li odběratel u pokladny v hotovosti nebo kartou, je faktura uhrazena
v okamžiku, kdy vznikne. Registrovat úhradu zvlášť je jen příležitost na ni
zapomenout — a otevřená faktura se pak objeví v pohledávkách i v upomínkách.

Modul přidá do platebních režimů OCA (`account_payment_mode`) jednu volbu:
faktura, jejíž platební režim ji má, se **při zaúčtování automaticky uhradí v
plné výši** v deníku určeném platebním režimem.

## Nastavení {#setup}

*Účetnictví → Konfigurace → Payment Modes* (modul nemá český překlad, proto
jsou jeho popisky anglicky). Vytvořte nebo otevřete platební režim, například
*Hotově* nebo *Kartou*:

| Pole | Hodnota |
|---|---|
| Payment Type | Inbound pro faktury odběratelům |
| Link to Bank Account | **Fixed** |
| Fixed Bank Journal | deník, do kterého peníze přicházejí — pokladna u hotovosti, zúčtovací deník karet u karet |
| **Register payment on validation** (*registrovat úhradu při zaúčtování*) | zaškrtnuto |

Zaškrtávací políčko se zobrazí, jen je-li *Link to Bank Account* nastaveno na
*Fixed*, a režim s ním nelze uložit bez pevného deníku.

Platební režim nastavte na faktuře (pole *Payment Mode*) nebo jako výchozí
platební režim odběratele na kontaktu, aby jej nové faktury dostaly samy.

## Co se stane při zaúčtování {#usage}

Zaúčtuje-li se faktura, jejíž platební režim má volbu **Register payment on
validation**:

- vytvoří se úhrada na **celou zbývající částku** a spáruje se s fakturou,
  přes standardního průvodce Odoo pro registraci úhrady — stejná úhrada,
  jakou byste zaregistrovali ručně;
- v pevném deníku platebního režimu;
- s **datem faktury** (chybí-li, s datem účtování).

Faktura je pak *Zaplaceno*, nebo *V platbě*, používá-li deník účet
nezúčtovaných příjmů a čeká na bankovní výpis.

Stejně to funguje u dobropisů odběratelům, přijatých faktur a účtenek s
takovým platebním režimem. Faktura, která je už uhrazena nebo na ní nic
nezbývá, zůstane beze změny. Více faktur zaúčtovaných najednou dostane každá
vlastní úhradu.

## Omezení {#limitations}

- Úhrada je vždy na celou částku. U částečně zaplaceného prodeje použijte
  platební režim bez této volby a úhradu zaregistrujte sami.
- Úhrada má datum faktury, ne okamžiku zaúčtování. Zaúčtujete-li fakturu se
  starším datem, bude mít starší datum i úhrada.
- Nelze-li úhradu vytvořit — například deník nemá vhodnou platební metodu —
  nezaúčtuje se ani faktura.
- Modul úhradu jen zaznamená. Nevystaví účtenku z pokladního systému a
  nekomunikuje s platebním terminálem.
