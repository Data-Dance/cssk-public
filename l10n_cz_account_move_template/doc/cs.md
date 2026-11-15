---
title: CZ předkontace interních dokladů
summary: Hotové české předkontace pro interní doklady — peníze na cestě přes účet 261 a přeúčtování schváleného výsledku hospodaření — které z jedné zadané částky vytvoří vyrovnaný koncept účetního zápisu.
verified: 19.0.1.0.0
---

## K čemu slouží {#purpose}

Některé zápisy nemají zdrojový doklad, ze kterého by Odoo účty odvodilo:
hotovost odvedená z pokladny do banky, zisk nebo ztráta přeúčtované poté, co
valná hromada schválila účetní závěrku. Účetní je účtuje interním dokladem,
obvykle podle zavedené předkontace.

Tento modul takové předkontace dodává jako **účetní vzory** modulu OCA
`account_move_template` pro společnosti s českou účtovou osnovou. Vyberete
vzor, zadáte jednu částku a dostanete vyrovnaný **koncept** zápisu.

**Co to není.** V českých účetních programech se *předkontace* obvykle volí
**na dokladu** — na faktuře, bankovním výpisu, pokladním dokladu — a určuje,
jak se doklad zaúčtuje. Modul OCA na žádný doklad navázaný není: pouze sestaví
nový ruční zápis. Faktury, banka a pokladna dál berou účty z Odoo samotného —
z produktu nebo kategorie produktu, z účtů pohledávek a závazků partnera,
z fiskální pozice, nastavení daní, deníku a párovacích modelů. Seznam
předkontací z jiného programu se proto většinou převádí na tyto objekty, ne
na vzory.

## Vzory {#templates}

Vytvářejí se v deníku *Různé* společnosti (kód `general` v osnově). Řádek 1
je částka, kterou zadáte; řádek 2 ji přebírá.

| Vzor | Má dáti (řádek 1) | Dal (řádek 2) |
|---|---|---|
| Výběr z pokladny (na peníze na cestě) | účet převodů likvidity (261…) | účet pokladního deníku |
| Příjem na bankovní účet (z peněz na cestě) | účet bankovního deníku | účet převodů likvidity (261…) |
| Výběr z bankovního účtu (na peníze na cestě) | účet převodů likvidity (261…) | účet bankovního deníku |
| Vklad do pokladny (z peněz na cestě) | účet pokladního deníku | účet převodů likvidity (261…) |
| Přeúčtování schváleného zisku (431 na 428) | 431000 Výsledek hospodaření ve schvalovacím řízení | 428000 Nerozdělený zisk minulých let |
| Přeúčtování schválené ztráty (431 na 429) | 429000 Neuhrazená ztráta minulých let | 431000 Výsledek hospodaření ve schvalovacím řízení |

Čtyři vzory pro peníze na cestě tvoří dvě poloviny převodu mezi pokladnou
a bankou: výběr jeden den, vklad jiný den, mezeru překlenuje účet 261.
Používají účty, na které společnost skutečně účtuje:

- **Peníze na cestě**: účet *převodů likvidity*, který Odoo vytvoří spolu
  s osnovou (účet 261, například 261001, nastavený jako účet interních převodů
  společnosti), ne 261000: v české osnově Odoo je 261000 přechodný účet banky,
  na kterém čekají nespárované řádky výpisů.
- **Banka a pokladna**: účet prvního bankovního a prvního pokladního deníku
  společnosti (Odoo dává každému deníku vlastní, například 221001). Dokud
  společnost pokladní deník nemá, používají pokladní vzory souhrnný účet
  211000; po jeho vytvoření změňte pokladní řádky na jeho účet.

Dva vzory pro výsledek hospodaření navazují na rozhodnutí o zisku nebo
ztrátě, jakmile je výsledek uzavřeného roku na účtu 431.

Názvy vzorů jsou české ve všech jazycích: Odoo názvy vzorů nepřekládá.

## Nastavení {#setup}

Vzory se vytvoří při nahrání české osnovy do společnosti a při instalaci pro
společnosti, které ji už mají. Společnost bez deníku *Různé* z osnovy se
přeskočí. Opakovaná instalace vzor nikdy nezdvojí ani nevrátí vaši úpravu.

Před prvním použitím otevřete každý vzor v nabídce *Účetnictví → Konfigurace
→ Účetnictví → Účetní vzory (předkontace)* (nabídka vyžaduje práva správce
účetnictví) a zkontrolujte:

- **Bankovní a pokladní účty.** Vzory berou účet prvního bankovního
  a pokladního deníku. Máte-li více bankovních účtů, zkopírujte vzor pro každý
  z nich a změňte jeho řádek.

Vzory jsou běžné záznamy: přejmenujte je, změňte účty, přidejte řádky nebo
vytvořte nové podle své vnitřní směrnice.

## Zaúčtování zápisu {#usage}

1. *Účetnictví → Účetnictví → Vytvořit zápis podle předkontace*, nebo tlačítko
   **Vytvořit účetní zápis** na formuláři vzoru.
2. Vyberte vzor a klikněte na **Další**.
3. Zkontrolujte datum, deník, označení a partnera a na nabídnutém řádku zadejte
   částku.
4. Klikněte na **Vytvořit účetní zápis**.

Zápis se vytvoří jako **koncept**; zkontrolujte ho a zaúčtujte jako obvykle.

## Omezení {#limitations}

- Vzory vytvářejí jen nové ruční zápisy; nelze je připojit k faktuře,
  bankovnímu výpisu ani pokladnímu dokladu a nemění, jak se tyto doklady
  účtují.
- Jeden bankovní a jeden pokladní účet na vzor; viz [Nastavení](#setup).
- Výchozí sada je záměrně malá. Nepokrývá například podíly na zisku, příděly
  do fondů ze zisku ani úhradu ztráty společníky; ty si doplňte podle potřeb
  společnosti.
- Přiřazení účtů zkontrolujte se svou účetní.
