---
title: CZ daňové odpisové skupiny
summary: Šest českých odpisových skupin 1–6 se sazbami rovnoměrného odpisování, koeficienty zrychleného odpisování a mimořádnými odpisy podle § 30a pro daňový odpisový plán.
verified: 19.0.1.0.3
---

## K čemu slouží {#purpose}

Nahraje české zákonné odpisové skupiny do modulu daňových odpisů
[module:account_asset_tax](module:account_asset_tax). S nimi může česká
společnost zatřídit majetek do skupiny a nechat si vypočítat daňový odpisový
plán podle českých pravidel: plná sazba prvního roku bez ohledu na měsíc
zařazení, zvýšené sazby v prvním roce, zrychlené odpisování ve všech
skupinách a mimořádné odpisy bezemisních vozidel ve skupině 2.

Jak se plán počítá a co s ním dál dělat, popisuje
[návod k daňovým odpisům](module:account_asset_tax#board).

## Právní rámec {#legal}

[Zákon č. 586/1992 Sb., o daních z příjmů](law:cz/1992/586):

- § 30 odst. 1 — odpisové skupiny a minimální doby odpisování; do které
  skupiny majetek patří, určuje příloha č. 1 zákona;
- § 30 odst. 2 — rovnoměrné nebo zrychlené odpisování, stanovené pro každý
  nově pořízený majetek a neměnné po celou dobu odpisování;
- § 31 odst. 1 — maximální roční odpisové sazby, včetně zvýšených sazeb
  prvního roku podle písm. b) až d);
- § 32 odst. 1 — koeficienty pro zrychlené odpisování;
- § 30a — mimořádné odpisy bezemisních vozidel pořízených od 1. 1. 2024 do
  31. 12. 2028 prvním odpisovatelem: 60 % a 40 % za 24 měsíců.

## Odpisové skupiny {#groups}

| Skupina | Minimální doba odpisování | Rovnoměrná sazba — první rok / další roky / zvýšená vstupní cena (%) | Koeficient zrychleného odpisování — první rok / další roky / zvýšená zůstatková cena | Mimořádné (§ 30a) |
|---|---|---|---|---|
| 1 | 3 roky | 20 / 40 / 33,3 | 3 / 4 / 3 | — |
| 2 | 5 let | 11 / 22,25 / 20 | 5 / 6 / 5 | povoleno |
| 3 | 10 let | 5,5 / 10,5 / 10 | 10 / 11 / 10 | — |
| 4 | 20 let | 2,15 / 5,15 / 5,0 | 20 / 21 / 20 | — |
| 5 | 30 let | 1,4 / 3,4 / 3,4 | 30 / 31 / 30 | — |
| 6 | 50 let | 1,02 / 2,02 / 2,0 | 50 / 51 / 50 | — |

Zvýšené sazby rovnoměrného odpisování v prvním roce (§ 31 odst. 1 písm. b)
až d)) pro skupiny 1–3 jsou součástí výpočtu a volí se na majetku v poli
*Zvýšený odpis v 1. roce*:

| Zvýšení | Skupina 1 | Skupina 2 | Skupina 3 |
|---|---|---|---|
| +10 % | 30 / 35 | 21 / 19,75 | 15,4 / 9,4 |
| +15 % | 35 / 32,5 | 26 / 18,5 | 19 / 9 |
| +20 % | 40 / 30 | 31 / 17,25 | 24,4 / 8,4 |

(první rok / další roky, % vstupní ceny)

Záznamy se jmenují *Odpisová skupina 1* až *6* s kódy `CZ-1` až `CZ-6` a v
poli skupiny na majetku se zobrazují například jako
`CZ-2 — Odpisová skupina 2 (5 r.)`.

## Nastavení {#setup}

Instaluje se s modulem daňových odpisů a mostem k registru majetku
([module:account_asset_tax_oca](module:account_asset_tax_oca) v Community,
[module:account_asset_tax_ee](module:account_asset_tax_ee) v Enterprise).
Vyžaduje českou lokalizaci Odoo (`l10n_cz`). Nic se nenastavuje: skupiny jsou
v *Účetnictví → Konfigurace → Daňové odpisové skupiny* a karta majetku je
nabídne společnostem se zemí Česká republika. Hodnoty se při každé
aktualizaci modulu nahrají znovu, takže ruční změny aktualizaci nepřežijí.

## Omezení {#limitations}

- Nahrají se jen skupiny. Zatřídění majetku do skupiny je na vás; modul
  nenavrhuje skupinu podle produktu ani účtu.
- Sazba +20 % patří jen strojům pro zemědělství a lesnictví u poplatníka s
  převážně zemědělskou a lesní výrobou, sazba +15 % jen zařízením uvedeným v
  § 31 odst. 3 a všechny tři jen prvnímu odpisovateli; nic z toho se
  nekontroluje.
- Mimořádné odpisy jsou povoleny jen ve skupině 2 jako skupině silničních
  vozidel; zda je vozidlo bezemisní a podmínky splňuje, musíte ověřit sami.
- Plán zaokrouhluje na haléře, nikoli na celé koruny nahoru, jak vyžaduje
  zákon; tuto a další odchylky uvádí
  [návod k daňovým odpisům](module:account_asset_tax#limitations).
