---
title: Česká republika — výchozí profily majetku
summary: Deset hotových profilů majetku pro českou společnost, jeden pro každý odpisovaný účet majetku z osnovy, každý s vlastním účtem oprávek a s odpisy na účet 551.
verified: 19.0.1.0.0
---

## K čemu slouží {#purpose}

V evidenci majetku pro Community (modul OCA
[module:account_asset_management](module:account_asset_management)) potřebuje
každý majetek **profil majetku**: ten určuje, na které účty se odpisy účtují
a jak dlouho se majetek odpisuje. Nová česká společnost má v osnově všechny
účty majetku, ale žádný profil, takže první majetek — zadaný ručně nebo
importovaný — nemá na co odkázat.

Tento modul dá každé české společnosti deset výchozích profilů, jeden pro
každý odpisovaný účet majetku české účtové osnovy. Týkají se jen **účetních
odpisů**. Daňové odpisy se řídí zákonnými odpisovými skupinami a řeší je
samostatně modul [module:account_asset_tax](module:account_asset_tax), který
se nainstaluje spolu s tímto modulem; samotné české skupiny dodává
[module:l10n_cz_account_asset_tax](module:l10n_cz_account_asset_tax).

## Právní rámec {#legal}

Podle [§ 28 odst. 6 zákona o účetnictví](law:cz/1991/563) sestavuje účetní
jednotka vlastní odpisový plán a majetek odpisuje v průběhu jeho používání,
nejvýše do výše jeho ocenění v účetnictví. Prováděcí
[vyhláška č. 500/2002 Sb.](law:cz/2002/500) doplňuje:

- § 56 odst. 2: nelze-li dobu použitelnosti goodwillu nebo nehmotných
  výsledků vývoje odhadnout, zvolí účetní jednotka dobu odpisování 60 až
  120 měsíců;
- § 6 odst. 3 písm. c): goodwill se odpisuje rovnoměrně nejpozději do
  60 měsíců;
- § 56 odst. 11: pozemky, umělecká díla a sbírky, povolenky na emise
  a preferenční limity se **neodpisují**.

Doby odpisování v těchto profilech jsou proto **výchozí hodnoty pro váš
odpisový plán, ne zákonné údaje**. Před potvrzením prvního majetku je
porovnejte se svou vnitřní směrnicí.

## Profily {#profiles}

Každý profil účtuje odpisy na účet **551000** (*Odpisy dlouhodobého
nehmotného a hmotného majetku*) v deníku různých operací, rovnoměrně, jedním
zápisem za měsíc:

| Profil (název, jak se zobrazuje) | Účet majetku | Oprávky | Roky |
|---|---|---|---|
| Nehmotné výsledky vývoje | 012000 | 072000 | 5 |
| Software | 013000 | 073000 | 3 |
| Ostatní ocenitelná práva | 014000 | 074000 | 6 |
| Goodwill | 015000 | 075000 | 5 |
| Ostatní dlouhodobý nehmotný majetek | 019000 | 079000 | 5 |
| Stavby | 021000 | 081000 | 30 |
| Hmotné movité věci a jejich soubory | 022000 | 082000 | 5 |
| Pěstitelské celky trvalých porostů | 025000 | 085000 | 10 |
| Dospělá zvířata a jejich skupiny | 026000 | 086000 | 5 |
| Jiný dlouhodobý hmotný majetek | 029000 | 089000 | 5 |

Nastavení profilu: *Metoda výpočtu* Lineární, *Časová metoda* Doba odpisování
(roky nebo datum konce), *Délka období* Měsíc, *Prorata Temporis* zapnuto.
První rok proto dostane jen svůj podíl ročního odpisu, od data zahájení
odpisování do konce roku — OCA tento podíl počítá ve dnech — a ne celý roční
odpis za majetek uvedený do užívání v listopadu. U nehmotného majetku
(012–019) pořízeného od roku 2021 na tom záleží dvakrát: zákon o daních
z příjmů už daňové odpisy nehmotného majetku nezná, takže do základu daně
vstupují jeho účetní odpisy. Datum zahájení nastavte na první den měsíce, od
kterého váš plán odpisuje (měsíc uvedení do užívání, nebo měsíc následující),
a dostanete celé měsíce.

Profil se nevytváří pro:

- **031 Pozemky**, **032 Umělecká díla a sbírky**, **016 Povolenky na emise**
  a **017 Preferenční limity**: nic na nich se neodpisuje a profil by tvrdil
  dobu použitelnosti, kterou nemají;
- **027 Oceňovací rozdíl k nabytému majetku**: odpisuje se (rovnoměrně
  180 měsíců, § 7 odst. 10 vyhlášky), ale vzniká jen při nabytí obchodního
  závodu a účtuje se na 557, ne na 551. Profil si vytvořte ručně, až ho
  budete potřebovat.

**Žádný profil nemá daňovou odpisovou skupinu.** *Sledovat daňové odpisy* je
vypnuto a *Daňová odpisová skupina* je u všech prázdná, a to záměrně: účet
o skupině nerozhoduje — stavba může být ve skupině 4, 5 nebo 6, movitá věc
v 1, 2 nebo 3 — a chybná výchozí hodnota by potichu vytvářela chybné daňové
odpisy.

## Nastavení {#setup}

Profily se vytvoří pro každou společnost s českou účtovou osnovou: při
nahrání osnovy a při instalaci pro společnosti, které ji už měly. Profil,
který společnost už má, se nikdy nevytváří znovu ani nepřepisuje, takže vaše
úpravy pozdější aktualizace přežijí. Společnost, která některý z použitých
účtů smazala nebo přečíslovala, se přeskočí (v logu serveru je varování)
a profily si musí vytvořit ručně.

Po instalaci v nabídce *Fakturace → Konfigurace → Majetky → Profily majetku*:

1. **Upravte doby odpisování** podle svého odpisového plánu. *Délku období*
   změňte na *Rok*, pokud odpisy účtujete jednou ročně; *Prorata Temporis*
   nechte zapnuté, pokud váš plán v prvním roce opravdu neúčtuje celý roční
   odpis.
2. **U profilů, jejichž majetek patří celý do jedné odpisové skupiny**,
   zaškrtněte *Sledovat daňové odpisy* a vyberte *Daňovou odpisovou skupinu*.
   Majetek vytvořený z profilu potom skupinu převezme (viz
   [module:account_asset_tax](module:account_asset_tax#oca)). Jinak pole
   nechte prázdné a skupinu nastavte na každém majetku.
3. Vytvořte další profily tam, kde jeden účet obsahuje majetek s velmi
   rozdílnou dobou použitelnosti (například několik profilů na 022000).

## Omezení {#limitations}

- Doby odpisování jsou výchozí hodnoty, ne zákon, a jsou stejné pro každou
  společnost. Nezávisí na daňové odpisové skupině.
- OCA krátí první rok **podle dnů** od data zahájení odpisování, ne podle
  celých měsíců: zahájení 1. července dává 184/365 ročního odpisu, ne 6/12.
  Začnete-li prvního dne měsíce, jde o rozdíl několika dnů.
- Existujícího majetku se modul nedotýká. Pozdější změna profilu nemění
  majetek, který z něj už byl vytvořen.
- Jen pro evidenci majetku Community: modul vyžaduje
  [module:account_asset_tax_oca](module:account_asset_tax_oca), a proto ho
  nelze nainstalovat společně s modulem `account_asset` z Odoo Enterprise.
