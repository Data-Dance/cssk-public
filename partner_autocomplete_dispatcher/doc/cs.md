---
title: Automatické doplňování partnerů ze státních registrů (CZ/SK)
summary: Doplňuje kontakty z českých a slovenských registrů místo placené služby Odoo a registr volí podle státu partnera.
verified: 19.0.1.2.0
---

## K čemu slouží {#purpose}

Vlastní automatické doplňování partnerů v Odoo hledá firmy v placené službě
Odoo (IAP). Pro české a slovenské partnery je ale směrodatným zdrojem státní
registr, v němž se subjekt vyhledává podle IČO. Tento modul je přepínačem mezi
nimi: každé společnosti umožní zvolit si **poskytovatele** automatického
doplňování a vyhledávání podle názvu, vyhledávání podle DIČ i samotné vyplnění
kontaktu posílá tomuto poskytovateli.

Sám o sobě nic viditelného nedělá. Instaluje se spolu s jedním nebo oběma
poskytovateli:

| Poskytovatel | Registr | Státy | Návod |
|---|---|---|---|
| ARES.CZ | ARES, Administrativní registr ekonomických subjektů | CZ | [níže](#ares) |
| ORSF.SK | ORSF, otevřený souhrn slovenských registrů (RPO, ORSR, ŽRSR, RÚZ, Finančná správa) | SK | [module:partner_autocomplete_orsf_sk](module:partner_autocomplete_orsf_sk) |

## Nastavení {#setup}

1. Nainstalujte modul poskytovatele. Tento modul se nainstaluje s ním.
2. *Nastavení → Obecná nastavení*, blok **Kontakty**: musí být zapnuto
   **Automatické doplňování partnerů** (*Partner Autocomplete*).
3. Pod ním v poli **Provider** zvolte registr pro aktuální společnost. Odkaz
   Odoo na nákup kreditů nahradí právě tato volba. Nastavení konkrétního
   poskytovatele se zobrazí pod ní, je-li zvolen.

Poskytovatel se ukládá pro každou společnost zvlášť. Přepněte se do každé
společnosti a nastavte ho tam.

Dvě volby nejsou registry:

- **Odoo IAP** vrátí vyhledávání vlastní službě Odoo, přesně jako bez tohoto
  modulu. Každé vyhledávání partnera ze státu, jehož registr žádný
  nainstalovaný poskytovatel nečte, odchází do Odoo.
- **None** nehledá nic mimo národní registry. Partner ze státu některého
  poskytovatele se tam hledá i nadále (viz níže); vše ostatní nenajde nic a do
  Odoo se nic neodešle.

Do verze 19.0.1.2.0 se jako **None** označovala dnešní volba **Odoo IAP**:
společnost, která si ji zvolila, používá službu Odoo i nadále. Pokud to
nechcete, zvolte znovu **None**.

## Který registr se použije {#routing}

Nejprve rozhoduje stát, teprve potom volba společnosti:

- Poskytovatel uvádí státy, jejichž registr čte — ARES čte CZ, ORSF SK. Je-li
  **Země** kontaktu jednou z nich (nebo při hledání podle DIČ začíná číslo
  předponou tohoto státu), použije se tento poskytovatel **bez ohledu na volbu
  společnosti**. Slovenská společnost tak může doplnit českého dodavatele z ARES
  a naopak, jsou-li nainstalováni oba poskytovatelé.
- U jiného státu nebo bez státu se použije **Provider** společnosti.
- Když zvolíte návrh, údaje se načtou z téhož registru, který ho nabídl. Je to
  důležité, protože české i slovenské IČO má osm číslic.

## Vyplnění kontaktu {#usage}

Do pole s názvem nového kontaktu napište alespoň tři znaky názvu firmy nebo
její IČO, případně DIČ do pole **DIČ** (*Tax ID*), a vyberte jeden z návrhů.
Poskytovatel vyplní adresu, identifikátory a další údaje, které podporuje;
přesný seznam je v návodu poskytovatele.

Poskytovatel může vrátit i **bankovní účty** a **kontakty**. Modul proto do
formuláře společnosti (*Nastavení → Společnosti*) přidá dvě záložky, *Bank
Accounts* a *Contacts*, aby je automatické doplnění vlastní společnosti mohlo
vyplnit také. Když poskytovatel seznam nahrazuje (bankovní účty, seznamy z
registru), staré řádky se odstraní, nezdvojí.

## Aktualizace existujících kontaktů {#update}

V seznamu označte jeden nebo více kontaktů a spusťte *Akce → Update*. Každý
kontakt se znovu vyhledá ve svém registru a přepíše se tím, co uvádí registr.

Dotáže se registru, který u kontaktu zaznamenalo předchozí automatické
doplnění, jinak registru podle **Země** kontaktu, jinak **Provider**
společnosti — ve stejném pořadí jako při vyhledávání.

K vyhledání se použije číslo, které patří samotnému kontaktu:

- IČO, které u něj zaznamenalo předchozí automatické doplnění, nebo
- pole **IČO** (*Company ID*) — ale jen u společnosti nebo u fyzické osoby bez
  nadřazené společnosti (OSVČ). Kontaktní osoba ve firmě má v tomto poli IČO
  firmy, které tam zkopíruje Odoo, a **přeskočí se**: vyhledání tohoto čísla by
  osobu přepsalo názvem a adresou firmy.

Pokud jste označili více kontaktů nebo se něco nepodařilo, oznámení sečte
výsledky: *updated* (aktualizováno), *skipped* (nebylo podle čeho hledat), *with
no data returned* (registr nevrátil nic) a *failed* (příčina je v logu serveru).

Registry omezují, kolik úplných záznamů lze načíst za minutu, takže **Update**
na velkém výběru v polovině přestane vracet údaje. Projeví se to jako *with no
data returned*, ne jako chyba.

## Doplnění kontaktů při importu {#import}

Importovaný soubor může obsahovat sloupec **Import Enrich Company** s IČO.
Každý importovaný kontakt, který v něm má hodnotu, se při vytvoření vyhledá a
vyplní z registru. Ručně vytvořené kontakty se nikdy nevyhledávají bez vašeho
vědomí: uložení nové společnosti s vyplněným **IČO** vyhledání nespustí.

## ARES (Česká republika) {#ares}

Modul [module:partner_autocomplete_ares_cz](module:partner_autocomplete_ares_cz)
čte veřejnou službu ARES Ministerstva financí. Není potřeba účet ani klíč.

- **Vyhledávání.** Podle názvu firmy: prvních pět shod ve tvaru *název, obec
  (IČO)*. IČO zadané jako číslice tuto firmu nabídne. České DIČ zadané do pole
  **DIČ** firmu najde, je-li to DIČ právnické osoby (*CZ* + osmimístné IČO) a
  ARES jí toto DIČ potvrdí.
- **Vyplní:** název, ulici, PSČ, obec, zemi a **DIČ** tak, jak ho uvádí ARES.
- **Nastavení** (zobrazí se, je-li ARES poskytovatelem společnosti):

  | Nastavení | Co dělá |
  |---|---|
  | IČO | Pole kontaktu, do kterého se zapíše IČO. Ve výchozím stavu prázdné, takže se IČO nikam neuloží, dokud pole nezvolíte — obvykle *IČO* (*Company ID*). |
  | Prevailing activity (CZ-NACE 2025) | Pole kontaktu, do kterého se zapíše převažující činnost z kopie statistického registru (RES) v ARES. Je-li nainstalován modul [module:partner_nace](module:partner_nace), nastaví se automaticky na *NACE (main activity)*. Stojí jeden požadavek navíc; prázdné = nenačítá se. |

- **Omezení.** ARES neumožňuje hledat podle DIČ; DIČ fyzické osoby (deset
  číslic, odvozené z rodného čísla) nemá IČO, podle kterého by se dalo hledat,
  a nic nenajde. ARES vrací DIČ bez ohledu na to, zda je firma právě
  plátcem DPH; před uplatněním režimu přenesení daňové povinnosti si ověřte
  její registraci. Bankovní účty a kontaktní osoby se nevyplňují.

## Omezení {#limitations}

- Prázdná odpověď poskytovatele vypadá stejně, ať firma neexistuje, registr
  nefunguje, nebo byl dosažen limit požadavků. Rozliší je log serveru.
- Popisky tohoto modulu nejsou přeložené.
