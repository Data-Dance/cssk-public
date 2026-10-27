---
title: Fio banka — bankové výpisy
summary: Každú hodinu sťahuje pohyby a oficiálne číslované výpisy z API Fio banky do bankového denníka, so symbolmi VS/KS/SS a účtami protistrany.
verified: 19.0.2.4.1
---

## Na čo slúži {#purpose}

S týmto modulom sa denník Fio banky plní sám: Odoo sa každú hodinu opýta API
Fio na nové pohyby a vytvorí riadky výpisu s účtom protistrany, platobnými
symbolmi a správou. Nie je čo sťahovať ani importovať. Funguje rovnako v
edícii Community aj Enterprise a pre české aj slovenské účty vo Fio.

Potrebuje pripojenie nastavené podľa modulu
[module:account_fio](module:account_fio#setup): **token na čítanie** pri
denníku.

## Zapnutie {#setup}

1. Na bankovom denníku (*Účtovníctvo → Konfigurácia → Účtovníctvo → Účtovné
   denníky*) nastavte pole **Bankové pohyby** (*Bank Feeds*) na **Fio banka
   API**. Denník nastavený na Fio bez tokenu na čítanie nemožno uložiť.
2. V časti **Fio banka** sa zobrazí pravý stĺpec *Bank statements*. Zvoľte
   **Režim sťahovania Fio** (pozri nižšie) a v režime pohybov aj **Dní
   spätného čítania Fio**.
3. Stlačte **Stiahnuť hneď** a stiahnite prvú dávku. Odvtedy beží plánovaná
   akcia *Fio: pull bank statements* každú hodinu.

Keďže pole *Bankové pohyby* má jedinú hodnotu, Fio a vlastná banková
synchronizácia Odoo Enterprise nemôžu napĺňať ten istý denník súčasne — každý
pohyb by sa naimportoval dvakrát. Denník napĺňaný z Fio navyše prestane na
riadiacom paneli Účtovníctva vyzývať na „pripojenie banky“.

Samotné tokeny sa dajú používať aj vtedy, keď má pole *Bankové pohyby* inú
hodnotu: denník môže odosielať platby do Fio a výpisy dostávať inak.

## Režimy sťahovania {#modes}

| Režim sťahovania Fio | Čo urobí každý beh | Na čo sa hodí |
|---|---|---|
| **Pohyby (opakovane čitateľný rozsah dátumov)** — predvolený | načíta pohyby od *dnes − dni spätného čítania* do dneška a pridá tie, ktoré Odoo ešte nemá | každodenné párovanie; vynechaný beh či reštart nenechá dieru |
| **Oficiálne číslované výpisy** | zistí od Fio číslo posledného výpisu a stiahne každý výpis, ktorý Odoo ešte nemá (najviac 12 za beh); z každého vznikne bankový výpis s názvom `<číslo>/<rok>` s počiatočným a konečným zostatkom podľa banky | účtovnú závierku: kontrola zostatku v Odoo porovnáva s dokladom, ktorý vydala banka |
| **Od záložky uloženej na tokene** | stiahne všetko od záložky, ktorú Fio vedie na tokene, a posunie ju | len s tokenom, ktorý nič iné nepoužíva |

Poznámky:

- **Dni spätného čítania** (predvolene 3): prekryv nič nestojí, lebo už
  naimportované pohyby sa vynechajú.
- **Zoskupovať pohyby Fio do výpisov** (len v režime pohybov, predvolene
  vypnuté): jeden výpis na každý deň s pohybmi, s názvom `<kód
  denníka>/<dátum>`, ktorého počiatočný a konečný zostatok sa dopočíta zo
  zostatku, ktorý Fio hlási na začiatku rozsahu, a z predchádzajúcich pohybov.
  Znova načítaný deň pribudne na výpis, ktorý už má, takže každý výpis sedí so
  svojimi zostatkami.
- **Oficiálne výpisy, prvý beh**: stiahne sa len posledný výpis. Na prelome
  roka modul začne znova výpisom č. 1 nového roka. Staršie výpisy a zvyšok
  predchádzajúceho roka stiahnete cez *Stiahnuť rozsah…*.
- **Záložka** je uložená vo Fio, na tokene. Čokoľvek iné, čo s tým istým
  tokenom číta pohyby — iný program, kolega pri skúšaní — ju posunie a tieto
  pohyby do Odoo nikdy neprídu.

## Ručné stiahnutie rozsahu {#backfill}

**Stiahnuť rozsah…** na denníku (aj v ponuke *Akcia* denníka) otvorí
sprievodcu *Stiahnuť z Fio*:

- *Pohyby v rozsahu dátumov*: dátumy od–do (predvolene posledných 7 dní);
- *Oficiálne číslované výpisy*: rok a prvé a posledné číslo výpisu.

Sprievodca vopred povie, koľko volaní požiadavka znamená — pri jednom volaní
za 30 sekúnd trvá rok pohybov rozdelený po mesiacoch približne šesť minút.

**Staršie ako 90 dní**: Fio také údaje poskytne, len kým je pre token v
internetbankingu odomknutá celá história (*Nastavení → API*, zámok), a
odomknutie platí **desať minút**. Sprievodca vás požiada, aby ste históriu
najprv odomkli a zaškrtli *História odomknutá v internet bankingu*; tlačidlo
**Stiahnuť** sa zobrazí až potom.

## Čo sa zapíše na riadok výpisu {#mapping}

| Fio | Odoo |
|---|---|
| ID pohybu | kľúč importu riadku a *ID pohybu Fio* |
| Datum | dátum (dátum zaúčtovania, ako ho uvádza Fio) |
| Objem | suma |
| Protiúčet + Kód banky | účet protistrany `číslo/kód banky`, podľa ktorého sa hľadá partner |
| Název protiúčtu | názov partnera |
| VS, KS, SS | polia symbolov (s modulom [module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols#bank-statements)) a značky `VS:…` v popise |
| Zpráva pro příjemce, inak Komentář, inak Uživatelská identifikace, inak Typ | popis (prvé vyplnené) |
| Typ | typ transakcie |
| Reference plátce | referencia |
| ID pokynu | *ID pokynu Fio* |
| Upřesnění v tvare `20.00 EUR` | pôvodná suma a mena platby vykonanej v inej mene |

Celý záznam z Fio sa uloží aj pri riadku. Duplicity sa rozpoznávajú len podľa
ID pohybu. ID pokynu zdieľa prevod so svojím poplatkom aj platba s neskorším
stornom, preto sa zámerne nepoužíva.

## Keď niečo zlyhá {#errors}

- Neúspešné plánované sťahovanie zapíše do chatteru denníka *Naplánované
  sťahovanie z Fio zlyhalo: …*; ostatné denníky sa stiahnu aj tak.
- Pohyb v inej mene, než má denník, zastaví sťahovanie pre tento denník:
  každý menový účet vo Fio potrebuje vlastný denník v tejto mene s vlastným
  tokenom.
- *Stiahnuť hneď* oznámi, koľko nových pohybov prišlo, alebo že nebolo nič
  nové. *Posledné stiahnutie z Fio* sa aktualizuje pri každom dokončenom
  sťahovaní, aj keď nič nenašlo.

## Obmedzenia {#limitations}

- **Prechod zo súborov GPC na API** nerozpozná pohyby už naimportované z GPC:
  obe cesty používajú iné kľúče importu. Prejdite na hranici dňa —
  naimportujte posledný výpis GPC a sťahovanie spustite nasledujúci deň.
- **Zoskupovať pohyby Fio do výpisov**: denné výpisy sú výpisy Odoo, nie
  doklady banky; pre výpisy číslované a odsúhlasené samotným Fio používajte
  *Oficiálne číslované výpisy*. Riadky naimportované pred zapnutím
  zoskupovania sa na výpis nepresunú, takže deň, ktorý niektoré z nich má,
  nebude sedieť. Ak nesedia už údaje Fio za daný rozsah, výpisy z tohto behu sa
  vytvoria bez zostatkov.
- Pôvodná suma platby v cudzej mene sa číta len z poľa *Upřesnění* v presnom
  tvare `20.00 EUR`; čokoľvek iné ostane len v uloženom zázname. Na skutočnom
  účte s viacerými menami to ešte treba overiť.
- V oficiálnom režime stiahne jeden beh najviac 12 chýbajúcich výpisov; dlhšia
  medzera sa doplní počas viacerých behov alebo cez *Stiahnuť rozsah…*.
- V edícii Enterprise modul pridá dva základné moduly OCA
  (`account_statement_base`, `account_statement_import_base`) pre kľúč importu
  a párovanie partnerov.
