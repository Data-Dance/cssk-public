---
title: Rozpad stĺpcov MIS Builder
summary: Rozdelí stĺpec MIS Builder na jeden stĺpec za každý denník, partnera, spoločnosť, produkt alebo iné pole, a za nimi súčet.
verified: 19.0.1.1.0
---

## Na čo slúži {#purpose}

V [module:mis_builder](module:mis_builder) sa výkaz so stĺpcom za každý denník,
partnera alebo spoločnosť musel skladať ručne: jeden stĺpec za každú hodnotu,
každý s vlastným analytickým filtrom, a udržiavať ho pri pribúdajúcich
hodnotách. Tento modul umožní jedinému stĺpcu rozdeliť sa podľa ľubovoľného
poľa účtovných položiek.

## Nastavenie {#setup}

Otvorte výkaz MIS (*Účtovníctvo › Výkazy › MIS Reports*) a na karte *Columns*
stĺpec. V časti **Rozpad**:

| Pole | Význam |
|---|---|
| Stĺpce podľa | Ľubovoľné pole typu many2one alebo výber na účtovných položkách stĺpca: *Denník*, *Partner*, *Spoločnosť*, *Produkt*, *Mena*, *Účet*, *Analytický účet*… Prázdne: bez rozpadu. |
| Najviac stĺpcov | Najväčší počet stĺpcov hodnôt (predvolene 12). Zobrazia sa hodnoty s najviac položkami; ostatné sú len v súčte. |

Pri výpočte výkazu sa stĺpec zmení na jeden stĺpec za každú hodnotu nájdenú
v jeho údajoch, pomenovaný podľa hodnoty a zoradený podľa názvu, a za nimi
samotný stĺpec ako **(spolu)**.

## Ako sa správa {#behaviour}

- Filtre stĺpca (dátumy, analytické filtre, filtre výkazu) platia pre každý
  stĺpec hodnoty.
- Súčtové a porovnávacie stĺpce, ktoré sa odvolávajú na rozpadnutý stĺpec,
  fungujú ďalej: použijú súčet.
- **Rozkliknutie** stĺpca hodnoty otvorí presne účtovné položky tejto hodnoty.
- **Poznámky** fungujú na každom stĺpci: poznámka pri stĺpci hodnoty patrí tejto
  hodnote, poznámka pri súčte celému stĺpcu.
- Položky bez hodnoty v poli (napríklad bez partnera) tvoria vlastný stĺpec
  *Nezadané*.

## Obmedzenia {#limitations}

Rozpadnúť sa dajú len stĺpce so zdrojom položiek: *Actuals* a alternatívne
zdroje, napríklad rozpočty vedené po účtoch, podľa ktoréhokoľvek poľa týchto
položiek. Rozpočty vedené po ukazovateľoch, súčtové ani porovnávacie stĺpce
nie.
