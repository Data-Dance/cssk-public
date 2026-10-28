---
title: Kontrolní hlášení / kontrolný výkaz DPH CZ/SK
summary: Obrazovky a výpočet společné pro české kontrolní hlášení a slovenský kontrolný výkaz DPH — oddíly ze zaúčtovaných dokladů, kontroly před exportem, XML ověřené proti XSD a záznam o podání.
verified: 19.0.2.4.0
---

## K čemu slouží {#purpose}

V Česku i na Slovensku podává plátce vedle daňového přiznání také přehled
jednotlivých daňových dokladů: české **kontrolní hlášení** (KH) a slovenský
**kontrolný výkaz DPH** (KV DPH). Formuláře se liší, práce je stejná —
zařadit každý zaúčtovaný doklad s DPH do správného oddílu, zkontrolovat ho,
vytvořit úřední XML a uschovat podanou kopii.

Tento modul je společná část: nabídka a formulář *Kontrolní hlášení*,
přiřazení oddílu každé položce deníku, proklik na zdrojové doklady, export a
záznam o podání. Sám nic nepodává. Oddíly, pravidla zařazení a úřední XML
dodává modul země:

- [module:l10n_cz_kh](module:l10n_cz_kh) — české kontrolní hlášení,
- [module:l10n_sk_kv_dph](module:l10n_sk_kv_dph) — slovenský KV DPH.

Právní rámec, verze formuláře a pravidla jednotlivých oddílů popisují jejich
stránky. Modul nepoužívá výkaznický engine Odoo Enterprise, takže v edici
Community i Enterprise funguje stejně.

## Nastavení {#setup}

Nainstalujte modul země; tento se nainstaluje s ním. Potom zkontrolujte:

- **DIČ společnosti** je vyplněné. Každý export ho uvádí jako identifikaci
  plátce a bez něj se nespustí.
- **Daně v režimu přenesení daňové povinnosti jsou rozpoznané.** Pravidla
  zařazení rozhodují podle příznaku daně *Přenesení daňové povinnosti*. Modul
  země ho nastaví na daních v režimu přenesení z české nebo slovenské účtové
  osnovy Odoo — při instalaci, při každém načtení osnovy pro novou společnost
  a při aktualizaci. U daně v režimu přenesení, kterou si vytvoříte sami,
  zaškrtněte **Přenesení daňové povinnosti** ve formuláři daně (*Pokročilé možnosti*);
  pole se zobrazuje u českých a slovenských daní.
- **Deník pro jeden oddíl.** Deník může poslat všechny své řádky s DPH do
  jednoho oddílu bez ohledu na pravidla: karta *Pokročilá nastavení* deníku,
  blok *Kontrolní hlášení*, pole **Přepis sekce kontrolního hlášení** —
  kód oddílu tak, jak ho uvádí tiskopis, např. `D.1` pro deník slovenské
  pokladny eKasa. U běžných deníků ho nechte prázdné.
- **Partneři mají vyplněné DIČ.** Většina podrobných oddílů identifikuje
  druhou stranu podle DIČ a export vyjmenuje každý doklad, jehož partnerovi
  chybí tam, kde ho formulář vyžaduje.

V *Účetnictví → Konfigurace → CZ/SK lokalizace* jsou dva seznamy:

| Nabídka | Co obsahuje |
|---|---|
| Verze kontrolního hlášení | Jeden záznam pro každou úřední strukturu formuláře: platnost, oddíly, XML šablonu a kořenový element, úřední XSD, proti které se export ověřuje, a hranici, která odděluje podrobné řádky od souhrnných. Dodávají je moduly zemí; zpravidla není třeba nic měnit. |
| Typy kontrolního hlášení | Druhy podání podle země (české *řádné / opravné / následné / následné/opravné*, slovenské *riadny / opravný / dodatočný*) a kód, který každý zapíše do XML. |

## Jak se doklad dostane do oddílu {#sections}

Každá zaúčtovaná položka deníku s daní dostane při zaúčtování oddíl
kontrolního hlášení. O tom, který, rozhodují pravidla modulu země; společné
je toto:

- **Faktury a opravné daňové doklady** mají směr (uskutečněné nebo přijaté
  plnění) daný typem dokladu. **Interní doklad** s DPH se zařadí podle svých
  daní, pokud všechny směřují stejně (samé prodejní, nebo samé nákupní daně);
  smíšený doklad se vynechá.
- **Přenesení daňové povinnosti se testuje jako první**, takže plnění, u
  kterého daň přiznává příjemce, nikdy nepropadne do běžných oddílů.
- **Daně na základě platby** (*Daňová způsobilost: Na základě platby*) se
  vykazují, až je platba učiní splatnými, ne při zaúčtování faktury. Řádek
  popisuje fakturu — partnera a číslo —, ale nese datum a částku platby,
  jeden řádek za každou platbu. Platba, jejíž spárování se ve stejném období
  zruší, se vynuluje.
- **Které období.** Uskutečněná plnění se vykazují v období podle *DUZP*,
  a pokud chybí, podle data zaúčtování. Přijaté doklady se vykazují v
  období, ve kterém se uplatňuje nárok na odpočet: podle data zaúčtování,
  nebo podle pozdějšího období zapsaného na dokladu (*Deklarované období
  DPH*). Stejné pravidlo používají moduly přiznání k DPH, takže se shodnou
  v tom, co do období patří.
- **Opravné daňové doklady.** Doklad vytvořený z faktury je s ní propojený a
  hlášení z tohoto propojení uvede číslo původního dokladu. U dokladu
  vytvořeného ručně zadejte číslo opravovaného dokladu do pole *Original
  document number* (karta *Další informace*; popisek je v této verzi
  anglicky). Pole se zobrazuje jen u opravných dokladů české nebo slovenské
  společnosti, které nejsou propojené s fakturou.
- **Interní doklady s DPH** mohou uvést, co jejich typ říct nedokáže: na kartě
  *Další informace* **Směr DPH** (uskutečněné, nebo přijaté plnění) a
  **Oprava DPH** (zda jde o opravný doklad). Je-li *Oprava DPH* nastavena na
  opravu, zobrazí se i *Original document number*. U faktur je nechte prázdné.
- **Po řádcích** má seznam položek deníku dokladu dva volitelné sloupce:
  **Sekce kontrolního hlášení** (uložený oddíl) a **DIČ pro kontrolní hlášení**,
  které pro jeden řádek nahradí DIČ partnera (zahraniční pobočka s vlastním
  číslem).

Oddíl je uložený na položce deníku. Pokud se změní něco, co pravidla
nevidí — například daňová země společnosti —, musí uložené oddíly přepočítat
správce; přepočet samotného hlášení nestačí.

## Příprava a podání hlášení {#usage}

*Účetnictví → Výkazy → Zákonné výkazy → Kontrolní hlášení*, potom *Nový*.

1. Vyplňte **společnost**, **období** (*Datum od*, *Datum do*) a **typ
   období** (měsíčně, nebo čtvrtletně); potom zvolte **verzi** (nabídnou se
   jen verze platné pro období) a **typ výkazu**. Období, které verze
   nepřipouští (její *Povolit měsíční* / *Povolit čtvrtletní*), se odmítne.
2. Klikněte na **Vypočítat**. Oddíly se naplní ze zaúčtovaných dokladů
   období a hlášení přejde do stavu *Náhled*. Každý oddíl má vlastní kartu.
   Dokud je hlášení v konceptu nebo náhledu, můžete počítat znovu, kolikrát
   je třeba; každý výpočet sestaví oddíly znovu z účetnictví.
3. **Kontrola.** Sloupec ✓ ukazuje, zda položky deníku za řádkem dávají
   dohromady jeho základ a daň. Tlačítko **Documents** na řádku otevře tyto
   položky seskupené podle dokladů, se základem, sazbou, DPH a odpočtem DPH
   každé z nich — poslední dvě se liší tam, kde je odpočitatelná jen část
   daně, například pohonné hmoty z 50 %. Souhrnné řádky ukážou všechny
   doklady, které sumarizují. Chybný řádek opravte na dokladu a počítejte znovu.
   Kde to modul země nabízí (slovenské oddíly kromě D.2), lze řádek opravit
   i v hlášení: zaškrtněte **Přepsat** a upravte částky; oprava přepočet
   přežije a znovu se použije na řádek se stejnou identitou, a ta, jejíž
   řádek zmizel, se oznámí v chatteru.
4. Klikněte na **Exportovat XML**. Před vytvořením souboru export ověří:
   - DIČ společnosti a kmenové údaje, které úřední formulář vyžaduje (modul
     země vyjmenuje chybné doklady);
   - věcná pravidla: podrobný řádek, jehož daň neodpovídá základu × sazbě,
     export zastaví, pokud se liší dvojnásobně a víc, a zdanitelný řádek se
     základem bez daně ho zastaví vždy. Menší rozdíly (zaokrouhlení) a
     ostatní upozornění ho nezastaví: zobrazí se ve žlutém pruhu nahoře na
     hlášení a v chatteru až do dalšího exportu.

   XML se pak ověří proti úřední XSD uložené na verzi a přiloží se k hlášení
   (*XML příloha*). Hlášení je ve stavu *Exportováno*. Po novém výpočtu můžete
   exportovat znovu.
5. **Podejte XML** finanční správě a klikněte na **Označit jako podané**.
   Podaná kopie se zmrazí (*Podané XML*, *Datum podání*), přidá se do historie
   podání a hlášení se zamkne proti přepočtu i exportu.
6. Označením jako podané se zároveň otevře záznam o **doručení**, který drží
   průběh doručení a potvrzení úřadu (viz
   [module:l10n_cssk_submission_base](module:l10n_cssk_submission_base)).
   Tlačítko **Podat** otevře nový a nechá zvolit kanál: ruční kanál portálu
   zaznamená, že hlášení bylo podáno ručně; s modulem
   [module:l10n_cz_epo](module:l10n_cz_epo) lze české podání podepsat a
   odeslat přímo na EPO. Odznak v záhlaví ukazuje stav doručení (popisy stavů
   jsou v této verzi anglicky).

Hlášení označené jako podané nelze smazat. Tlačítko *Porovnání* se objeví,
jakmile bylo hlášení porovnáno s účetnictvím nebo s jiným podáním.

## Opravy {#amendments}

- **Vrátit do konceptu** znovu otevře exportované nebo podané hlášení. Smí to
  jen administrátor účetnictví. Už podané kopie zůstávají v historii podání.
- **Opravné / následné** (české hlášení) nebo **Dodatočný / opravný**
  (slovenský výkaz) na podaném hlášení vytvoří nový koncept propojený s
  ním (*Opravuje*). Zvolte typ opravného podání (u kontrolního hlášení
  *následné*), opravte účetnictví a potom počítejte a exportujte jako obvykle.
  Jak se oprava vypočte, závisí na zemi: české *následné* kontrolní hlášení
  opakuje celé období, slovenský *dodatočný* kontrolný výkaz obsahuje jen
  změněné řádky. Viz stránky zemí.

**Historická podání** — hlášení převzatá z předchozího systému jako záznam
toho, co bylo podáno — mají stav *Historické podání*. Nelze je přepočítat,
exportovat ani podat.

## Omezení {#limitations}

- Tento modul sám nic nepodává; podává se ručně na portálu, nebo přes modul
  kanálu podání.
- Oddíl položky deníku je uložený. Po změně daňové země nebo po změně
  samotných pravidel je musí správce přepočítat dřív, než se hlášení počítají
  znovu.
- České karty oddílů *Přepsat* nenabízejí: české řádky vykazují sloupce
  podle sazeb, které přepis nenese. Opravte doklad.
- Pravidla zařazení jsou nejlepším možným odhadem a stránky zemí uvádějí, co
  je ještě třeba potvrdit s účetním. Každé hlášení před podáním zkontrolujte.
