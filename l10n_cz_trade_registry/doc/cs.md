---
title: CZ výpis z rejstříku (§ 435, stav, předmět podnikání)
summary: Uchovává zápis českého subjektu ve veřejném rejstříku jako data, skládá z nich údaj o zápisu, který na vaše doklady vyžaduje § 435 občanského zákoníku, a upozorní na partnery, které rejstřík už nevede jako aktivní.
verified: 19.0.1.0.0
---

## K čemu slouží {#purpose}

Český podnikatel musí na dokladech uvádět, ve kterém rejstříku je zapsán a
pod kterým oddílem a vložkou. Česká lokalizace Odoo má na to u společnosti
jediné textové pole **Zápis v obchodním rejstříku** (*Trade Registry*). Vyplní
se jednou a pak se na něj zapomene — a tiskne se dál i poté, co se změnilo
sídlo a s ním i soud.

Tento modul:

- uchovává tři údaje o zápisu — **Rejstřík**, **Rejstříkový soud** a
  **Spisovou značku** (oddíl a vložku) — jako samostatná pole u vaší
  společnosti i u kteréhokoli kontaktu;
- skládá z nich správnou češtinou údaj o zápisu a udržuje s ním v souladu pole
  **Zápis v obchodním rejstříku** společnosti, takže se tiskne na fakturách;
- u každého českého kontaktu ukáže, co o něm uvádí rejstřík: stav, datum
  vzniku a zániku, předmět podnikání a činnosti a předchozí názvy a sídla;
- na faktuře vydané i přijaté upozorní, pokud rejstřík vede partnera jako
  zaniklého, historického nebo pozastaveného.

Údaje se zadávají ručně, nebo je z ARES doplní modul
[module:partner_autocomplete_ares_cz](module:partner_autocomplete_ares_cz).

## Právní rámec {#legal}

[§ 435 odst. 1 občanského zákoníku](law:cz/2012/89#p435) ukládá každému
podnikateli uvádět na obchodních listinách a v rámci informací
zpřístupňovaných veřejnosti prostřednictvím dálkového přístupu — tedy na webu
— své jméno a sídlo. Dále:

- podnikatel zapsaný v **obchodním rejstříku** uvede údaj o tomto zápisu
  **včetně oddílu a vložky**;
- podnikatel zapsaný v jiném veřejném rejstříku uvede údaj o svém zápisu do
  tohoto rejstříku;
- podnikatel nezapsaný ve veřejném rejstříku uvede údaj o svém zápisu do jiné
  evidence — živnostník tedy zápis v živnostenském rejstříku;
- byl-li podnikateli přidělen identifikující údaj (IČO), uvede i ten.

Veřejných rejstříků je šest — obchodní rejstřík, spolkový rejstřík, nadační
rejstřík, rejstřík ústavů, rejstřík společenství vlastníků jednotek a rejstřík
obecně prospěšných společností (§ 1 zákona č. 304/2013 Sb.) — a každý vede
rejstříkový soud: Městský soud v Praze nebo krajský soud.

## Nastavení {#setup}

*Nastavení → Společnosti*, otevřete svou českou společnost. Nad polem **Zápis
v obchodním rejstříku** jsou tři nová pole:

| Pole | Příklad |
|---|---|
| Rejstřík | Obchodní rejstřík |
| Rejstříkový soud | Městský soud v Praze |
| Spisová značka | C 12345 — oddíl a vložka tak, jak je uvádí rejstřík |

Modul z nich složí údaj o zápisu a zapíše jej do pole **Zápis v obchodním
rejstříku**, které česká lokalizace Odoo tiskne na fakturách:

> Obchodní rejstřík vedený Městským soudem v Praze, oddíl C, vložka 12345

- Údaj jmenuje rejstřík a soud, který jej vede, místo aby říkal *zapsaná*
  nebo *zapsaný*; je proto správně u jakékoli právní formy.
- Soud se uvádí v 7. pádě (*Městský soud* → *Městským soudem*, *Krajský soud*
  → *Krajským soudem*). Znění *vedený … soudem* a *oddíl / vložka* se použije
  jen u šesti veřejných rejstříků.
- Jiný rejstřík nebo evidence se vypíše tak, jak jste jej zadali, s orgánem za
  čárkou a číslem jako *číslo zápisu: …*. Živnostník, který zadá jen
  *Živnostenský rejstřík*, dostane právě to.
- Číslo, které není oddílem a vložkou, se vytiskne celé jako *spisová
  značka …*.

**Vaše vlastní znění má přednost.** Pokud do pole **Zápis v obchodním
rejstříku** napíšete něco jiného, modul je od té chvíle nechá být. Složený
údaj je vidět a lze jej upravit také jako **Údaj o zápisu (§ 435)** u kontaktu
společnosti; úprava se tam promítne i do pole **Zápis v obchodním rejstříku**
a platí, dokud se některý ze tří údajů znovu nezmění. Vymazáním všech tří
údajů se vymaže i údaj, který modul zapsal.

## Rejstřík u kontaktu {#partner}

Záložka **Rejstřík (CZ)** u kontaktu v Česku (nebo bez země):

| Skupina | Pole |
|---|---|
| Zápis | Rejstřík, Rejstříkový soud, Spisová značka, Datum vzniku, Údaj o zápisu (§ 435) |
| Stav | Stav v rejstříku, Datum zániku, Rejstřík ověřen (kdy byl rejstřík naposledy načten) |

Pod nimi, doplněné z rejstříku a jen pro čtení:

- **Předmět podnikání a činnosti** — co zápis uvádí o tom, čím se subjekt
  zabývá (předmět podnikání, předmět činnosti, doplňková činnost, účel), vždy
  se dnem zápisu a dnem výmazu. Jde o vlastní znění zápisu, ne o statistický
  kód CZ-NACE.
- **Předchozí názvy a sídla** — dřívější názvy a sídla s dobou platnosti; hodí
  se při párování starého dokladu s dnešním partnerem.

Je-li nainstalován modul
[module:partner_autocomplete_ares_cz](module:partner_autocomplete_ares_cz),
vyplní se vše výběrem firmy z nabídky ARES nebo akcí *Akce → Update* u
kontaktu; nic se nenastavuje. Živnostník, který není v žádném veřejném
rejstříku, ale je v živnostenském rejstříku, dostane jako rejstřík
*Živnostenský rejstřík*.

## Partneři, kteří už nejsou aktivní {#dissolved}

Je-li **Stav v rejstříku** *Zaniklý*, *Historický* nebo *Pozastavený*:

- žlutý pruh nahoře na kontaktu říká, že subjekt není aktivní, s datem
  zániku, je-li známo; stav lze v seznamu kontaktů zobrazit jako sloupec;
- faktura, dobropis nebo účtenka společnosti, jejíž fiskální zemí je Česko,
  zobrazí upozornění se stavem, datem a dnem, kdy byl stav v rejstříku ověřen.
  U přijaté faktury dodá, že dodavatel v době plnění nemusel existovat, a že
  je tedy třeba ověřit nárok na odpočet daně;
- při zaúčtování takového dokladu se upozornění zapíše i do jeho komunikace.

Upozornění zaúčtování nikdy neblokuje. Konečná faktura nebo opožděná přijatá
faktura od zaniklého partnera může být zcela v pořádku; rozhoduje datum na
dokladu a to dokáže posoudit jen člověk.

Všechny takové partnery najednou uvidíte v *Účetnictví → Zákazníci →
Neaktivní subjekty (CZ)*, nebo pomocí filtru **Neaktivní subjekty (CZ)** v
kterémkoli seznamu kontaktů — zákazníků, dodavatelů i kontaktů.

## Omezení {#limitations}

- Česká lokalizace Odoo tiskne pole **Zápis v obchodním rejstříku** jen na
  fakturách, s popiskem *Zápis v obchodním rejstříku:*, a to i tehdy, když
  údaj jmenuje jiný rejstřík. § 435 se vztahuje i na objednávky, dopisy a web;
  tam údaj doplňte sami.
- Údaj záměrně nemá obvyklé znění *zapsaná v obchodním rejstříku vedeném …*.
  Dáváte-li mu přednost, napište je do pole **Zápis v obchodním rejstříku**.
- Skloňuje se jen *Městský soud* a *Krajský soud*. Cokoli jiného se vytiskne
  tak, jak bylo zadáno, což může znít toporně. Údaj si jednou zkontrolujte.
- Seznam uložených účetních závěrek chybí: jsou ve sbírce listin, kterou ARES
  neposkytuje.
- Stav je tak aktuální jako poslední dotaz do rejstříku; pravidelně se
  neobnovuje. Bez modulu pro ARES zůstanou stav, data a seznamy prázdné,
  dokud je nezadáte ručně.
