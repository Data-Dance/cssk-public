---
title: EPO — kontrola a podání na Finanční správu
summary: Podepíše česká podání kvalifikovaným certifikátem společnosti a odešle je do EPO — v testovacím režimu ke kontrole, nebo naostro k podání — a sleduje každé podání až do přijetí nebo odmítnutí.
verified: 19.0.1.0.1
---

## K čemu slouží {#purpose}

**EPO** (*Elektronická podání pro Finanční správu*) je elektronická podatelna
české daňové správy za portálem MOJE daně. Kromě webových formulářů a datové
schránky má rozhraní pro účetní software, *Podatelnu EPO*. To nezná uživatelské
účty ani klíče API: podání je XML zabalené do podpisu vytvořeného
**kvalifikovaným certifikátem** podatele a podpis je zároveň jeho identitou.

Modul přidává EPO jako **kanál** k záznamům podání modulu
[module:l10n_cssk_submission_base](module:l10n_cssk_submission_base). Každý
výkaz, který lze přes tento rámec podat, pak lze:

- **zkontrolovat** — podepsat a odeslat v testovacím režimu EPO, který provede
  kontroly EPO (podpis, strukturu, obsah) a nic nepodá;
- **podat** — podepsat a odeslat naostro, pokud to společnost povolí;
- **sledovat** — uchová se *potvrzení* a *podací číslo* a EPO se pravidelně
  dotazuje, zda finanční úřad podání přijal, nebo odmítl.

Mezi českými výkazy, které vytvářejí soubor EPO, a mohou tedy jít tímto
kanálem, jsou:

| Podání | Modul |
|---|---|
| přiznání k DPH (DPHDP3) | [module:l10n_cz_vat_return](module:l10n_cz_vat_return) |
| kontrolní hlášení (DPHKH1) | [module:l10n_cz_kh](module:l10n_cz_kh) |
| souhrnné hlášení (DPHSHV) | [module:l10n_cz_ec_sales](module:l10n_cz_ec_sales) |
| přiznání OSS (OSSEI1) | [module:l10n_cz_oss](module:l10n_cz_oss) |
| přiznání k dani z příjmů právnických osob | [module:l10n_cz_dppo](module:l10n_cz_dppo) |
| vyúčtování daně z příjmů ze závislé činnosti | [module:l10n_cz_hr_payroll_annual_tax_settlement](module:l10n_cz_hr_payroll_annual_tax_settlement) |

Kanál podepíše a odešle soubor, který výkaz vyexportoval; nekontroluje, zda jde
o formulář EPO.

## Právní rámec {#legal}

Podle [§ 71 odst. 1 daňového řádu (zákon č. 280/2009 Sb.)](law:cz/2009/280)
lze podání učinit elektronicky jen datovou zprávou podepsanou způsobem, se
kterým jiný právní předpis spojuje účinky vlastnoručního podpisu, odeslanou
z datové schránky nebo s jinak ověřenou identitou podatele. Daňový subjekt se
zpřístupněnou datovou schránkou zřizovanou ze zákona nebo s povinností mít
účetní závěrku ověřenou auditorem musí formulářová podání — mezi nimi daňová
přiznání — činit jen elektronicky ([§ 72 odst. 6](law:cz/2009/280)). Podání na
technické zařízení správce daně je učiněno dnem, kdy správci daně došlo,
a zařízení jeho přijetí potvrdí s časovým údajem
([§ 73 odst. 1 a 3](law:cz/2009/280)). Modul používá první cestu: podepsanou
datovou zprávu.

## Nastavení {#setup}

Vše níže vidí jen uživatelé ve skupině **Zákonná podání: podávat**.

1. **Certifikát.** *Účetnictví → Konfigurace → Účetnictví → Certifikáty EPO*,
   potom *Nový*. Nahrajte kvalifikovaný certifikát **i s privátním klíčem**
   jako soubor `.p12` / `.pfx`, jak ho vydala certifikační autorita (I.CA,
   PostSignum, eIdentity), a jeho heslo. Soubor má obsahovat i mezilehlé
   certifikáty vydavatele. Při uložení modul soubor otevře a zobrazí subjekt,
   vydavatele a platnost; soubor, který nejde otevřít, odmítne.
2. **Společnost.** *Nastavení → Uživatelé a společnosti → Společnosti*,
   společnost, záložka **EPO podání**, skupina **Odesílání do EPO**:

| Pole | Účel |
|---|---|
| Podpisový certifikát EPO | Certifikát, kterým se podání společnosti podepisují. |
| Povolit podávání přes EPO | Vypnuto (výchozí): EPO slouží jen ke **kontrole** podání. Zapnuto: podání EPO zařazené do fronty se **podá naostro**. |

Zbytek záložky EPO podání (oprávněná osoba, sestavil, zástupce) patří k českým
výkazovým formulářům a je popsán u nich.

Kdo má certifikát, může podávat jménem společnosti, proto soubor certifikátu
a heslo může číst a měnit jen skupina, která podává. Ostatní účetní vidí, že
certifikát existuje, ne jeho obsah.

## Kontrola a podání {#usage}

Samotný výkaz — třeba přiznání k DPH — se připraví a vyexportuje jako obvykle.
Potom:

1. Na výkazu klikněte na **Podat**. Je-li nainstalován víc než jeden kanál,
   Odoo místo vytvoření podání ukáže podání tohoto výkazu; vytvořte nové
   s kanálem **EPO — Finanční správa (podepsané, přímo)**. Kanál se nabízí,
   jen je-li zemí daňové příslušnosti společnosti Česko. Označení výkazu jako
   podaného také otevře podání, a to s kanálem *Portál úřadu — podáno ručně*;
   dokud je v konceptu, můžete mu kanál přepnout na EPO.
2. **Zkontrolovat v EPO**. Soubor se podepíše a odešle
   v testovacím režimu. Výsledek se uloží na podání, záložka **Kontrola EPO**:
   *Bez chyb*, *Jen varování* nebo *Chyby*, se seznamem zpráv EPO a jeho odpovědí jako přílohou XML. Kontrola
   nikdy nic nepodá a nemění stav podání; můžete ji opakovat, kolikrát chcete.
3. **Zařadit do fronty** a potom **Odeslat nyní** —
   nebo počkat na plánovanou úlohu, která zařazená podání odesílá každých pět
   minut. Tím se podává naostro, a to jen tehdy, je-li zapnuto *Povolit
   podávání přes EPO*. Podepsaný soubor se uchová na podání. EPO odpoví:
   - **potvrzením** — uloží se na záložku **Potvrzení** a jeho podací číslo se
     stane *Číslem podání úřadu*; podání je *Doručeno*;
   - u velkého podání zpracovávaného mimo linku *ID předání* — podání je
     *Doručeno* a potvrzení se stáhne později;
   - **seznamem chyb** — podání přejde do stavu *Selhalo* se zprávami
     EPO a uživateli, který podání vytvořil, se naplánuje aktivita.
4. **Přijetí.** Úloha jednou za hodinu se EPO ptá na stav každého doručeného
   podání, dokud ho finanční úřad **nepřijme** nebo **neodmítne**, a podle toho
   ho nastaví na *Přijato* nebo *Zamítnuto*.
5. Jakmile EPO podání převezme, výkaz, který je ještě ve stavu *Exportováno*,
   se automaticky **označí jako podaný** — jeho podaná kopie se zmrazí — a
   podací číslo se zkopíruje do jeho pole *Reference podání*.

*Doručeno* znamená, že EPO podání převzalo; teprve *Přijato* znamená, že ho
přijal finanční úřad. Formulář podání to u doručeného podání výslovně uvádí.

## Když se něco nepovede {#errors}

- **EPO není dostupné** (spojení se vůbec nenavázalo): podání se vrátí do fronty
  a opakuje se po 1, 5, 15, 60 a 180 minutách, potom selže.
- **Výsledek není známý** — požadavek mohl do EPO dojít, ale řádná odpověď se
  nevrátila: podání **selže a neopakuje se**, protože opakované odeslání by
  mohlo přiznání podat dvakrát. Než cokoli odešlete znovu, ověřte podání na
  portálu MOJE daně. Totéž platí pro jakoukoli neočekávanou chybu, i pro chybu
  při zaznamenání potvrzení EPO poté, co EPO podání přijalo: podání selže,
  zpráva uvede podací číslo a varuje, abyste je znovu neodesílali.
- **Certifikát vypršel** nebo ještě neplatí: modul odmítne podepsat.

## Omezení {#limitations}

- Kontroly EPO jsou podmnožinou kontrol finančního úřadu. Čistá kontrola není
  zárukou, že podání bude přijato; modul toto upozornění opakuje.
- Zpracování odpovědí ostré služby je napsáno podle zveřejněného popisu
  rozhraní EPO a z tohoto kódu nebylo proti ostré službě ověřeno.
- Modul kontroluje platnost certifikátu, ne to, zda je kvalifikovaný; to ověří
  EPO.
- EPO nevrací PDF podání.
