---
title: Místo prodeje — česká EET 2.0
summary: Eviduje každou zaplacenou objednávku Místa prodeje v českém systému EET 2.0 v okamžiku platby — jen kontaktní část platby —, tiskne potvrzovací kód na účtenku a sděluje zákazníkovi, kdy bude tržba oznámena dodatečně.
verified: 19.0.1.3.1
---

## K čemu slouží {#purpose}

S tímto modulem oznamuje každá pokladna Místa prodeje své tržby do českého
systému **EET 2.0**, jak zákon vyžaduje: když pokladní potvrdí platbu, Odoo
odešle datovou zprávu, krátce počká na **potvrzovací kód** (*POK*) a vytiskne
jej na účtenku. Právní rámec, nastavení společnosti, certifikáty a způsob,
jakým se zprávy opakují a uchovávají, popisuje
[module:l10n_cz_eet2](module:l10n_cz_eet2), na němž tento modul staví.

## Nastavení {#setup}

### 1. Platební metody {#payment-methods}

*Místo prodeje → Konfigurace → Platební metody*: každá metoda má příznak
**EET 2.0 Contact Payment**, ve výchozím stavu zapnutý. Hotovost, platební
terminály a QR kód zobrazený u pokladny jsou kontaktní platby a zůstávají
zapnuté. Příznak vypněte u metody, která představuje peníze přijaté na dálku —
bankovní převod přicházející později, platební bránu u objednávek k vyzvednutí
—, aby se neevidovala.

### 2. Pokladna {#till}

*Místo prodeje → Konfigurace → Místo prodeje*, otevřete pokladnu, záložka
**EET 2.0**:

| Pole | Co dělá |
|---|---|
| EET 2.0 PoS ID (id_pokl) | Označení pokladního zařízení odesílané za tuto pokladnu, nejvýše 20 znaků; při prázdném poli název pokladny. Každá pokladna jedné evidenční jednotky potřebuje vlastní. |
| EET 2.0 Unit ID (id_jednotky) | Evidenční jednotka, do níž pokladna patří; při prázdném poli výchozí jednotka společnosti. |

Přepínač na úrovni společnosti, EIČ, prostředí a certifikát pocházejí
z [nastavení základního modulu](module:l10n_cz_eet2#settings).

## Co se eviduje {#scope}

Objednávka se eviduje, je-li EET 2.0 u společnosti zapnuta a její platební
řádky uhrazené metodami označenými jako kontaktní dávají dohromady něco jiného
než nulu. **Eviduje se jen tato kontaktní část**, nikoli celková částka
objednávky: objednávka zaplacená napůl hotově a napůl metodou označenou jako
vzdálená oznámí hotovostní polovinu a objednávka bez kontaktních peněz neoznámí
nic a napíše to do své diskuse. Vrácené peníze nazpět se vyruší.

- **Časem tržby** je čas poslední platby, tedy okamžik, na který zákon hledí
  u platby kartou nebo QR kódem.
- **Vratka** zaeviduje záporný součet peněz vrácených kontaktními metodami —
  storno v podobě, kterou zákon předepisuje.
- **Dárkové karty a elektronické peněženky** prodané nebo uplatněné u pokladny
  se oznamují ve dvou zvláštních položkách, je-li nainstalován
  [module:l10n_cz_eet2_pos_loyalty](module:l10n_cz_eet2_pos_loyalty), což se
  stane samo, jakmile je nainstalován věrnostní modul.
- **Jedna zpráva na objednávku.** Objednávka nikdy nenese dvě živé zprávy
  o prodeji; opakované odeslání použije tu, kterou má.

## U pokladny a na účtence {#receipt}

Když pokladní potvrdí platbu, pokladna se nejvýše na **mezní dobu odezvy**
společnosti (výchozí 5 sekund) zastaví, dokud se zpráva odesílá. Účtenka pak
tiskne blok **EET 2.0** s POK; na playgroundu přidá *NEPRODUKČNÍ / TEST*.

Když brána včas neodpoví nebo je pokladna offline, prodej přesto proběhne
a účtenka vytiskne **Tržba bude odeslána dodatečně**. Naplánovaná úloha odesílá
dál, dokud brána nepřijme, do 48 hodin a poté každou hodinu, takže u pokladny
není třeba nic dělat. Zpráva, kterou brána odmítla natrvalo, netiskne nic.

Objednávka v back office (*Místo prodeje → Objednávky*) ukazuje svůj **EET 2.0
Status** a **EET 2.0 POK** a tlačítko **Resend to EET** pro objednávku, jejíž
zpráva ještě nebyla přijata.

## Omezení {#limitations}

- Účtenka nese POK jen tehdy, dorazil-li před tiskem; účtenka vytištěná znovu
  později ukazuje kód, který objednávka do té doby má.
- Které metody jsou kontaktní platby, je vaše rozhodnutí; metoda označená jako
  vzdálená se neeviduje nikdy, ani když zákazník stojí u pultu.
- Pokladna neeviduje tržby za jiného poplatníka.
