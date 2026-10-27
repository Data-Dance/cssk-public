---
title: Připomínka vypršující převedené dovolené (CZ/SK)
summary: Denní připomínka zaměstnancům, že převedená dovolená, jejíž platnost akruální plán brzy ukončí, vyprší — jako aktivita a e-mail.
verified: 19.0.1.1.0
---

## K čemu slouží {#purpose}

Akruální plán v Odoo může převádět nevyčerpanou dovolenou do dalšího roku a
převedené dny nechat k určitému datu vypršet. Slovenské plány dovolené
mzdových modulů to dělají na konci následujícího roku; české plány dovolenou
převádějí bez vypršení. Odoo to ukazuje jen pasivně, na přehledu aplikace
*Volno*. Tento modul připomíná aktivně: jednou denně vyhledá převedenou
dovolenou, která brzy vyprší, a aktivitou a e-mailem sdělí zaměstnanci, o kolik
dní jde a do kdy. Schvalující volno nebo nadřízený dostane vlastní aktivitu.

Závisí jen na aplikaci Odoo *Volno* (`hr_holidays`), takže funguje s každým
akruálním plánem, ve kterém převedené dny vyprší, s kterýmkoli mzdovým jádrem
i úplně bez mezd.

## Právní rámec {#legal}

Ani v jedné zemi nevyčerpaná dovolená koncem následujícího roku nepropadá.
Vyprší převedený zůstatek v Odoo podle nastavení akruálního plánu. Zákon
naopak ukládá zaměstnavateli, aby byla dovolená vyčerpána:

- **Česká republika.** Nemůže-li být dovolená vyčerpána v roce, ve kterém na
  ni vzniklo právo, nebo byla-li její část převedena na písemnou žádost
  zaměstnance, je zaměstnavatel povinen určit ji tak, aby byla vyčerpána
  **nejpozději do konce následujícího kalendářního roku**
  ([§ 218 odst. 3 zákoníku práce](law:cz/2006/262)). Není-li čerpání určeno
  do **30. června** následujícího roku, má právo je určit i zaměstnanec,
  s písemným oznámením alespoň 14 dnů předem (§ 218 odst. 4). Dovolenou,
  kterou nebylo možné vyčerpat ani do konce následujícího roku pro pracovní
  neschopnost nebo mateřskou či rodičovskou dovolenou, určí zaměstnavatel po
  skončení těchto překážek (§ 218 odst. 5).
- **Slovensko.** Zaměstnavatel musí dovolenou, kterou nebylo možné vyčerpat
  v jejím roce, poskytnout tak, aby skončila **nejpozději do konce
  následujícího kalendářního roku**; neurčí-li její čerpání do **30. června**
  toho roku, může si je určit zaměstnanec, s písemným oznámením nejméně 30 dní
  předem ([§ 113 ods. 2 Zákonníka práce](law:sk/2001/311#paragraf-113.odsek-2)).
  Dovolenou, které bránila mateřská, otcovská nebo rodičovská dovolená nebo
  pracovní neschopnost, poskytne po jejich skončení
  ([§ 113 ods. 3 a 4](law:sk/2001/311#paragraf-113.odsek-3)).

Připomínka je tedy výzvou naplánovat dovolenou před lhůtou, kterou musí
dodržet zaměstnavatel. Žádá zaměstnance, aby se s vedoucím domluvil, kdy
dovolenou vyčerpá, a uvádí, že podle zákoníku práce dovolená nepropadá; datum
v ní je den, kdy akruální plán dny odebere ze zůstatku v Odoo.

## Nastavení {#setup}

Nic není třeba nastavovat. Chování mění dva systémové parametry
(*Nastavení → Technická nastavení → Systémové parametry*, režim vývojáře):

| Parametr | Výchozí | Co dělá |
|---|---|---|
| `l10n_cssk_leave_expiry.lead_days` | `60` | Kolik dní před datem vypršení se připomínka pošle. |
| `l10n_cssk_leave_expiry.send_email` | `True` | Zda se kromě aktivity pošle i e-mail. `False`, `0`, `no` nebo `off` ho vypnou. |

Plánovaná akce *Dovolená: Upozornit na vypršující převedenou dovolenou
(CZ/SK)* běží jednou denně (*Nastavení → Technická nastavení → Opakované
akce*). E-mailová šablona je *Dovolená: Připomínka vypršující dovolené*; její
znění můžete upravit.

Aby se připomínka dostala k zaměstnanci, potřebuje zaměstnanec **Příslušného
uživatele** (pro aktivitu) a **Pracovní email** (pro e-mail). Aby se o ní
dozvědělo personální oddělení, potřebuje zaměstnanec schvalujícího volno nebo
nadřízeného s uživatelem.

## Jak připomínka funguje {#usage}

Plánovaná akce každý den vezme alokace ve stavu *Schváleno*, *Ke
schválení* nebo *Druhé schválení*, jejichž převedené dny vyprší mezi dneškem a dneškem plus předstih
(výchozí 60 dní). Alokace akruálního plánu, který převod nepovoluje, se
vynechají: jde o roční limity typu „vyčerpej, nebo propadne“, například
slovenské dny na lékařské vyšetření či doprovod, ve kterých se nic
nepřevádí.

U každé alokace spočítá dny, které by skutečně vypršely: převedený zůstatek
minus dovolenou čerpanou z alokace od té doby. Samotné Odoo toto odečtení dělá
až v den vypršení, proto může být počet v připomínce nižší než hodnota uložená
na alokaci. Nezbývá-li nic, připomínka se nepošle.

Jinak

1. naplánuje na kartě **zaměstnance** aktivitu **Vypršující dovolená**
   s termínem v den vypršení, s počtem dní, typem volna a datem, přidělenou
   vlastnímu uživateli zaměstnance a adresovanou zaměstnanci (*„Máte …“*);
2. naplánuje na téže kartě druhou aktivitu **Vypršující dovolená** pro
   *Schvalujícího volno*, a není-li, pro uživatele nadřízeného, formulovanou
   o zaměstnanci (*„<Zaměstnanec> má …“*). Děje se to pokaždé, i když
   zaměstnanec uživatele má a první aktivitu dostal. Je-li schvalujícím nebo
   nadřízeným vlastní uživatel zaměstnance, druhá aktivita se nevytvoří;
3. je-li to zapnuto, pošle stejný text na *Pracovní email* zaměstnance,
   v jazyce zaměstnance. U typu volna, které se žádá v hodinách, je počet
   uveden v hodinách.

Na každé datum vypršení se připomíná **jednou**: alokace si pamatuje datum,
na které byla naposledy připomenuta, a nová připomínka přijde až u nového
převedeného zůstatku s novým datem vypršení. Nepodaří-li se doručit nic —
zaměstnanec nemá uživatele, není schvalující ani nadřízený s uživatelem,
chybí pracovní e-mail — alokace se jako připomenutá neoznačí a další denní
běh to zkusí znovu.

U slovenských plánů mzdových modulů převedené dny vyprší 364 dní po převodu
1. ledna, tedy 31. prosince následujícího roku (v přestupném roce
30. prosince), takže připomínka ve výchozím nastavení přijde na začátku
listopadu. České plány vypršení nenastavují, jejich alokace proto připomínku
nedostanou.

## Omezení {#limitations}

- **Jedna připomínka na jedno vypršení.** Jakmile byla připomínka doručena,
  druhá blíže k termínu nepřijde.
- Připomínka je jen tak dobrá jako akruální plán: alokace bez akruálního plánu
  nebo plán bez vypršení převedených dní ji nikdy nedostane.
- Odesílatelem e-mailu je e-mail společnosti typu volna, a nemá-li typ volna
  společnost, uživatel plánované akce.
