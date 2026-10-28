---
title: Štatutárne podania CZ/SK — doručenie
summary: Záznam o tom, ako sa každé štatutárne podanie dostalo k úradu — kanál, pokusy, doručenie, prijatie — a miesto na potvrdenky, ktoré to dokazujú.
verified: 19.0.1.1.1
---

## Na čo slúži {#purpose}

Export daňového priznania alebo kontrolného výkazu a jeho označenie ako
podaného (pozri [životný cyklus podania](module:l10n_cssk_core#filings))
zmrazí podané XML. Nezaznamená však, **ako** sa dostalo k finančnej správe,
či bolo doručené a čo prišlo späť. To pridáva tento modul: záznam o
**doručení** (*submission*) pre každé odoslanie podania, s jeho stavom,
pokusmi a **potvrdenkami** — potvrdenkou o podaní a doručenkou —, ktoré
zostávajú v Odoo, a nie v niečej e-mailovej schránke.

Ide o rámec. Sám ponúka jediný kanál: podanie **ručne na portáli** úradu,
ktoré sa v Odoo potvrdí. Elektronické kanály pridávajú iné moduly. Štatutárne
tlačivá lokalizácie si ho nainštalujú samy.

## Doručené nie je prijaté {#states}

| Stav | Význam |
|---|---|
| Koncept | pripravené, neodoslané |
| Vo fronte | čaká na odoslanie alebo na ďalší pokus |
| Odosiela sa | prebieha pokus |
| **Doručené** | **kanál** potvrdil, že podanie prevzal — prenos fungoval |
| **Prijaté** | **úrad** podanie prijal — podanie platí |
| Zamietnuté | úrad ho odmietol |
| Zlyhalo | nedalo sa odoslať; opakovanie nepomôže alebo sa minuli pokusy |
| Zrušené | stiahnuté skôr, než sa dostalo k úradu |

Kanál, ktorý odpoveď úradu nevidí, skončí v stave *Doručené* a formulár to
výslovne uvedie: doručenie kanálu ešte nie je prijatie úradom.

## Kto môže čo {#access}

Dve skupiny v časti *Účtovníctvo* v nastaveniach používateľa:

- **Štatutárne podania: pripravovať** — vidí doručenia a ich potvrdenky.
- **Štatutárne podania: podávať** — navyše ich zaraďuje do fronty, odosiela,
  potvrdzuje a ruší. Zahŕňa práva správcu účtovníctva.

## Podanie výkazu {#usage}

1. Na výkaze kliknite na *Označiť ako podané*. Automaticky sa otvorí doručenie
   v stave **Koncept**, ktoré ukazuje na podané XML, aby mali potvrdenky kam
   prísť.
2. Prípadne tlačidlo *Podať* na exportovanom alebo podanom výkaze otvorí nové
   doručenie; ak ho môže podať viac kanálov, vyberiete si kanál. Ponúkajú sa
   len kanály, ktoré môžu podávať za spoločnosť výkazu — napríklad EPO len pre
   českú spoločnosť.
3. **Ručné podanie** (kanál *Portál úradu — podané ručne*): XML podajte sami
   na portáli finančnej správy a potom kliknite na **Potvrdiť podanie**. Odoo
   zaznamená, kto a kedy podanie potvrdil, a doručenie prejde do stavu
   *Doručené*.
4. **Elektronický kanál**: kliknite na **Zaradiť do frontu**. Doručenie sa
   odošle do niekoľkých minút, alebo hneď tlačidlom **Odoslať teraz**.
   Doručenie sa odošle raz, aj keď sa *Odoslať teraz* stretne s plánovaným
   odosielaním: odošle ho ten, kto ho prevezme prvý, a *Odoslať teraz* oznámi,
   že sa práve odosiela — o chvíľu ho obnovte a uvidíte výsledok.
5. Potvrdenky priložte na karte **Potvrdenia** a podacie číslo zapíšte do poľa
   **Číslo podania úradu**.
6. **Ručné podanie bolo prijaté**: keď máte potvrdenie úradu, priložte ho na
   karte **Potvrdenia** a kliknite na **Potvrdiť prijatie**. Doručenie prejde do
   stavu *Prijaté*. Bez priloženého potvrdenia tlačidlo odmietne pokračovať:
   potvrdenie je dôkaz.

**Doručenie a výkaz zostávajú v súlade:**

- Doručenie, ktoré ešte nebolo odoslané, nesie vždy **aktuálny** export
  výkazu. Ak výkaz vrátite do návrhu, prepočítate a znova exportujete,
  doručenie pri najbližšom overení, zaradení do frontu alebo potvrdení prevezme
  nové XML (a zapíše to do chatu). Doručenie, ktoré už je vo fronte, sa
  **neodošle**, ak bol výkaz medzitým vrátený alebo znova exportovaný: zlyhá so
  správou, aby ste ho zaradili do frontu znova.
- Keď sa doručenie dostane k úradu — kanál ho doručí alebo potvrdíte ručné
  podanie —, výkaz, ktorý je ešte v stave *Exportované*, sa **označí ako
  podaný** (jeho podaná kópia sa zmrazí) a číslo podania úradu sa skopíruje do
  jeho poľa *Referencia podania*.

Všetky doručenia nájdete v *Účtovníctvo → Výkazy → Zákonné výkazy →
Doručenia*, filtrované na tie, ktoré ešte neboli prijaté; filter *Vyžaduje
pozornosť* ukáže zlyhané a zamietnuté. Formulár výkazu zobrazuje stav
aktuálneho doručenia ako štítok.

## Opakovanie a zlyhanie {#retries}

Na pozadí bežia dve plánované akcie:

- *Štatutárne podania: odoslať front* — každých 5 minút odošle, čo je na rade;
- *Štatutárne podania: zisťovať prijatie* — každú hodinu sa kanálov, ktoré to
  vedia, opýta, či doručené podania boli prijaté.

Dočasná chyba, ktorú kanál rozpozná (nedostupná brána, spojenie sa nepodarilo
nadviazať), vráti doručenie do fronty a skúsi to znova po 1, 5, 15, 60 a 180
minútach. Potom, alebo hneď pri chybe, ktorú opakovanie nevyrieši (chybné
údaje, chýbajúci certifikát), prejde doručenie do stavu **Zlyhalo**, chyba sa
zobrazí vo formulári a osobe, ktorá ho otvorila, vznikne aktivita — podľa
možnosti priamo na výkaze. Odstráňte príčinu a znova kliknite na *Zaradiť do
frontu*.

**Neočakávaná** chyba sa neopakuje: mohla nastať až potom, čo sa podanie
dostalo k úradu, a opakované odoslanie by podalo priznanie dvakrát. Doručenie
zlyhá so správou, že výsledok nie je známy a treba to overiť na portáli.
Najprv to skontrolujte na portáli; znova ho zaraďte do frontu, len ak tam
podanie nie je.

Doručenie v stave *Doručené* alebo *Prijaté* sa zrušiť nedá: podajte opravu.

## Obmedzenia {#limitations}

- Doručenie nekontroluje lehotu na podanie.
- *Potvrdiť prijatie* zaznamená tvrdenie človeka podložené priloženým
  potvrdením; obsah prílohy nič nekontroluje.
