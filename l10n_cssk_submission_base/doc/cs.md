---
title: Zákonná podání CZ/SK — doručení
summary: Záznam o tom, jak se každé zákonné podání dostalo k úřadu — kanál, pokusy, doručení, přijetí — a místo pro potvrzení, která to dokládají.
verified: 19.0.1.1.1
---

## K čemu slouží {#purpose}

Export přiznání k DPH nebo kontrolního hlášení a jeho označení jako podaného
(viz [životní cyklus podání](module:l10n_cssk_core#filings)) zmrazí podané
XML. Nezaznamená však, **jak** se dostalo k finanční správě, zda bylo doručeno
a co přišlo zpět. To přidává tento modul: záznam o **doručení**
(*submission*) pro každé odeslání podání, s jeho stavem, pokusy a
**potvrzeními** — potvrzením o podání a doručenkou —, která zůstávají v Odoo,
a ne v něčí e-mailové schránce.

Jde o rámec. Sám nabízí jediný kanál: podání **ručně na portálu**, které se v
Odoo potvrdí. Elektronické kanály přidávají jiné moduly — například
[module:l10n_cz_epo](module:l10n_cz_epo) podává česká přiznání přímo na
podatelnu EPO Finanční správy. Zákonné formuláře lokalizace si ho nainstalují
samy.

## Doručeno není přijato {#states}

| Stav | Význam |
|---|---|
| Koncept | připraveno, neodesláno |
| Ve frontě | čeká na odeslání nebo na další pokus |
| Odesílá se | probíhá pokus |
| **Doručeno** | **kanál** potvrdil, že podání převzal — přenos fungoval |
| **Přijato** | **úřad** podání přijal — podání platí |
| Zamítnuto | úřad ho odmítl |
| Selhalo | nepodařilo se odeslat; opakování nepomůže nebo došly pokusy |
| Zrušeno | staženo dříve, než se dostalo k úřadu |

Kanál, který odpověď úřadu nevidí, skončí ve stavu *Doručeno* a formulář to
výslovně uvede: doručení kanálu ještě není přijetí úřadem.

## Kdo smí co {#access}

Dvě skupiny v části *Účetnictví* v nastavení uživatele:

- **Zákonná podání: připravovat** — vidí doručení a jejich potvrzení.
- **Zákonná podání: podávat** — navíc je zařazuje do fronty, odesílá,
  potvrzuje a ruší. Zahrnuje práva správce účetnictví.

## Podání výkazu {#usage}

1. Na výkazu klikněte na *Označit jako podané*. Automaticky se otevře doručení
   ve stavu **Koncept**, které ukazuje na podané XML, aby měla potvrzení kam
   přijít.
2. Případně tlačítko *Podat* na exportovaném nebo podaném výkazu otevře nové
   doručení; může-li je podat více kanálů, vyberete si kanál. Nabízejí se jen
   kanály, které mohou podávat za společnost výkazu — například EPO jen pro
   českou společnost.
3. **Ruční podání** (kanál *Portál úřadu — podáno ručně*): XML podejte sami
   na portálu (EPO, datová schránka) a potom klikněte na **Potvrdit podání**.
   Odoo zaznamená, kdo a kdy podání potvrdil, a doručení přejde do stavu
   *Doručeno*.
4. **Elektronický kanál**: klikněte na **Zařadit do fronty**. Doručení se
   odešle během několika minut, nebo hned tlačítkem **Odeslat nyní**.
   Doručení se odešle jednou, i když se *Odeslat nyní* setká s plánovaným
   odesíláním: odešle ho ten, kdo ho převezme první, a *Odeslat nyní* oznámí,
   že se právě odesílá — za chvíli ho obnovte a uvidíte výsledek.
5. Potvrzení přiložte na kartě **Potvrzení** a číslo podání zapište do pole
   **Číslo podání úřadu**.
6. **Ruční podání bylo přijato**: jakmile máte potvrzení úřadu, přiložte ho na
   kartě **Potvrzení** a klikněte na **Potvrdit přijetí**. Doručení přejde do
   stavu *Přijato*. Bez přiloženého potvrzení tlačítko odmítne pokračovat:
   potvrzení je důkaz.

**Doručení a výkaz zůstávají v souladu:**

- Doručení, které ještě nebylo odesláno, nese vždy **aktuální** export
  výkazu. Pokud výkaz vrátíte do konceptu, přepočtete a znovu exportujete,
  doručení při nejbližším ověření, zařazení do fronty nebo potvrzení převezme
  nové XML (a zapíše to do chatu). Doručení, které už je ve frontě, se
  **neodešle**, pokud byl výkaz mezitím vrácen nebo znovu exportován: selže se
  zprávou, abyste je zařadili do fronty znovu.
- Jakmile se doručení dostane k úřadu — kanál je doručí nebo potvrdíte ruční
  podání —, výkaz, který je ještě ve stavu *Exportováno*, se **označí jako
  podaný** (jeho podaná kopie se zmrazí) a číslo podání úřadu se zkopíruje do
  jeho pole *Reference podání*.

Všechna doručení najdete v *Účetnictví → Výkazy → Zákonné výkazy →
Doručení*, filtrovaná na ta, která ještě nebyla přijata; filtr *Vyžaduje
pozornost* ukáže selhaná a zamítnutá. Formulář výkazu zobrazuje stav
aktuálního doručení jako štítek.

## Opakování a selhání {#retries}

Na pozadí běží dvě naplánované akce:

- *Zákonná podání: odeslat frontu* — každých 5 minut odešle, co je na řadě;
- *Zákonná podání: zjišťovat přijetí* — každou hodinu se kanálů, které to
  umějí, zeptá, zda doručená podání byla přijata.

Dočasná chyba, kterou kanál rozpozná (nedostupná brána, spojení se
nepodařilo navázat), vrátí doručení do fronty a zkusí to znovu po 1, 5, 15, 60
a 180 minutách. Potom, nebo hned u chyby, kterou opakování nevyřeší (chybné
údaje, chybějící certifikát), přejde doručení do stavu **Selhalo**, chyba se
zobrazí ve formuláři a osobě, která ho otevřela, vznikne aktivita — podle
možnosti přímo na výkazu. Odstraňte příčinu a znovu klikněte na *Zařadit do
fronty*.

**Neočekávaná** chyba se neopakuje: mohla nastat až poté, co se podání
dostalo k úřadu, a opakované odeslání by přiznání podalo dvakrát. Doručení
selže se zprávou, že výsledek není znám a je třeba to ověřit na portálu.
Nejprve to zkontrolujte na portálu; znovu je zařaďte do fronty, jen pokud tam
podání není.

Doručení ve stavu *Doručeno* nebo *Přijato* zrušit nelze: podejte opravu.

## Omezení {#limitations}

- Doručení nekontroluje lhůtu pro podání.
- *Potvrdit přijetí* zaznamená tvrzení člověka podložené přiloženým
  potvrzením; obsah přílohy nic nekontroluje.
