---
title: Slovenská účtovná lokalizácia — kompletná sada
summary: Nainštaluje slovenskú štatutárnu lokalizáciu jedným krokom, voliteľné časti ponúkne ako prepínače v nastaveniach a porovná výkazy DPH navzájom aj s účtovníctvom.
verified: 19.0.1.4.3
---

## Na čo slúži {#purpose}

Slovenská lokalizácia je rozdelená do mnohých modulov, aby si každá
spoločnosť nainštalovala len to, čo potrebuje. Tento modul je cesta jedným
kliknutím: jeho inštalácia prinesie štatutárne jadro pre slovenskú spoločnosť
a pridá prepínače pre voliteľné časti. Okrem toho pridáva tri **krížové
kontroly** medzi výkazmi DPH a účtovníctvom.

## Čo nainštaluje {#contents}

| Oblasť | Modul |
|---|---|
| Spoločné jadro: nastavenia, daňové úrady, životný cyklus podania | [module:l10n_cssk_core](module:l10n_cssk_core) |
| Slovenská štatutárna báza | [module:l10n_sk_statutory](module:l10n_sk_statutory) |
| Daňové priznanie k DPH | [module:l10n_sk_vat_return](module:l10n_sk_vat_return) |
| Kontrolný výkaz DPH | [module:l10n_sk_kv_dph](module:l10n_sk_kv_dph) |
| Súhrnný výkaz | [module:l10n_sk_ec_sales](module:l10n_sk_ec_sales) |
| Slovenská faktúra | [module:l10n_sk_invoice](module:l10n_sk_invoice) |
| Saldokonto a zápočty | [module:l10n_cssk_partner_balances](module:l10n_cssk_partner_balances) |
| Overenie IČ DPH v systéme VIES | [module:l10n_cssk_vies](module:l10n_cssk_vies) |
| Dohadné položky | [module:l10n_cssk_accrual](module:l10n_cssk_accrual) |
| Inventarizácia | [module:l10n_sk_inventory_verification](module:l10n_sk_inventory_verification) |

Každý z týchto modulov má vlastný návod.

## Voliteľné časti {#setup}

*Účtovníctvo → Konfigurácia → Nastavenia*, blok **Česká / slovenská
lokalizácia**. Zaškrtnite prepínač a uložte: Odoo modul nainštaluje.
Odškrtnutím ho znova odinštaluje.

| Prepínač | Nainštaluje | Poznámka |
|---|---|---|
| Synchronizácia kurzov (NBS/ECB) | [module:currency_rate_update_sk](module:currency_rate_update_sk) | denné kurzy NBS/ECB a kurzy bánk; len Community |
| Časové rozlíšenie | [module:l10n_sk_account_cutoff](module:l10n_sk_account_cutoff) | náklady a výnosy budúcich období (381–385); len Community |
| Kontrola spoľahlivosti dodávateľa | [module:l10n_sk_payment_reliability](module:l10n_sk_payment_reliability) | pred platbou overí zverejnený bankový účet dodávateľa |
| Dvojité odpisovanie | [module:l10n_sk_account_asset_tax](module:l10n_sk_account_asset_tax) | daňové odpisy popri účtovných |
| Spôsob A evidencie zásob | `l10n_sk_stock_account_method_a` | priebežné účtovanie zásob spôsobom A; dodáva sa v samostatnom repozitári |
| Zálohové faktúry | [module:l10n_sk_sale_order_advance_invoice](module:l10n_sk_sale_order_advance_invoice) | zálohové faktúry a daňové doklady k prijatej platbe |
| Účtovné vzory (interné doklady) | [module:l10n_sk_account_move_template](module:l10n_sk_account_move_template) | pomenované vzory MD/D pre interné doklady |
| Účtovná závierka | [module:l10n_sk_fiscal_year_closing](module:l10n_sk_fiscal_year_closing) | uzavretie roka cez 710 / 702 a otvorenie cez 701 |
| Finančný prenájom | [module:l10n_sk_account_loan_oca](module:l10n_sk_account_loan_oca) | finančný prenájom (lízing) |
| Protokoly k majetku | [module:l10n_sk_asset_protocol_oca](module:l10n_sk_asset_protocol_oca) | zaraďovací a vyraďovací protokol |
| Dovoz tovaru (JCD) | [module:l10n_sk_jcd](module:l10n_sk_jcd) | colné vyhlásenie pri dovoze |
| Vozidlá a PHL | [module:l10n_sk_vehicle_expense](module:l10n_sk_vehicle_expense) | vozidlá a pohonné látky |
| Manažérske výkazy | [module:l10n_sk_mis_reports](module:l10n_sk_mis_reports) | manažérska výsledovka na MIS Builder; nie je to štatutárny výkaz |
| Vyťažovanie faktúr (AI) | [module:account_invoice_ai_extract](module:account_invoice_ai_extract) | načítanie došlých faktúr z PDF do návrhu dodávateľskej faktúry |
| Účtovná závierka (Súvaha, VZS) | [module:l10n_sk_fs](module:l10n_sk_fs) | súvaha a výkaz ziskov a strát pre register účtovných závierok |
| Daňové priznanie DPPO | [module:l10n_sk_dppo](module:l10n_sk_dppo) | daňové priznanie k dani z príjmov právnickej osoby |

Ak je nainštalovaná účtovná závierka aj DPPO, sám sa nainštaluje modul
[module:l10n_sk_dppo_fs](module:l10n_sk_dppo_fs), ktorý previaže výsledok
hospodárenia s daňovým priznaním.

V Odoo Enterprise sú prepínače kurzov a časového rozlíšenia skryté, lebo
Enterprise má vlastné.

## Krížové kontroly výkazov {#reconciliation}

Na formulároch výkazov sa po výpočte (v inom stave ako návrh) objavia tri
tlačidlá. Každé vytvorí alebo obnoví porovnanie na obrazovkách *Podané vs
vypočítané* z modulu [module:l10n_cssk_core](module:l10n_cssk_core), s
výsledkom pri každom riadku a miestom na odpoveď účtovníka.

| Na formulári | Tlačidlo | Porovná |
|---|---|---|
| Kontrolný výkaz DPH | *Porovnať s priznaním* | KV s daňovým priznaním za rovnaké obdobie |
| Súhrnný výkaz | *Porovnať s priznaním* | súhrnný výkaz s daňovým priznaním za rovnaké obdobie |
| Daňové priznanie k DPH | *Porovnať s účtovníctvom* | priznanie s účtom 343 a účtovou triedou 60 |

Použije sa vypočítané alebo exportované priznanie tej istej spoločnosti,
ktorého obdobie sa prekrýva — prednostne s presne rovnakým obdobím. Ak také
nie je, tlačidlo to oznámi; najprv vypočítajte priznanie.

**KV a priznanie.** Kontrolný výkaz nikdy neobsahuje celé priznanie — dodania
nezdaniteľným osobám, zjednodušené faktúry a podobné plnenia sú len v
priznaní —, preto musí byť KV v priznaní **obsiahnutý**, nie sa mu rovnať:

| Blok | Oddiely KV | Riadky priznania |
|---|---|---|
| Daň na výstupe | A.1 + C.1 | r. 02 + 02a + 04 |
| Samozdanenie | B.1 | r. 06, 06a, 08, 10, 10a, 10b, 12, 12a – 12e |
| Odpočítaná daň | B.2 + B.3.1 + B.3.2 + C.2 | r. 18 + 18a + 19 |

Menšia suma v KV sa zobrazí ako *Rozdiel je očakávaný*. **Väčšia** suma v KV
je nemožná a vykáže sa ako rozdiel s upozornením, aby ste skontrolovali
zatriedenie plnení.

**Súhrnný výkaz a priznanie.** Dodanie tovaru do iného členského štátu (kód
plnenia 0) sa musí rovnať riadku 14. Trojstranný obchod (kód 1) a služby (kód
2) nemajú v priznaní vlastný riadok a neporovnávajú sa.

**Priznanie a účtovníctvo.**

| Riadok | Porovná sa s | Výsledok |
|---|---|---|
| Daň na výstupe, r. 17 | DPH zaúčtovaná z daní na predaj v období | rozdiel, ak nesedí |
| Odpočítaná daň, r. 18 + 18a + 19 | DPH zaúčtovaná z daní na nákup v období | rozdiel, ak nesedí |
| Základ dane, r. 01 + 01a + 03 + 13 | obrat Dal účtovej triedy 60 | vždy len informatívne |

Základ dane a tržby sa oprávnene líšia (prijaté preddavky, dohadné položky,
nadobudnutie tovaru, finančné výnosy), preto tento riadok nikdy nie je
zistením.

Všade platí tolerancia 0,50 € alebo 0,1 % porovnávanej sumy, podľa toho, čo je
väčšie.

## Obmedzenia {#limitations}

- Krížové kontroly sú len poradné. Neblokujú export ani podanie.
- Kontrola KV predpokladá plný odpočet; pri odpočítaní koeficientom bloky
  odpočítanej dane nesedia.
- Kontrola voči účtovníctvu delí DPH na výstupnú a vstupnú podľa typu dane
  (predaj alebo nákup). Pri tuzemskom prenesení daňovej povinnosti, keď jedna
  faktúra nesie oboje, je rozdelenie približné.
- Prepínač modulu, ktorý na serveri nie je (spôsob A, účtovná závierka, DPPO),
  nerobí nič.
- Odinštalovanie tohto modulu neodinštaluje moduly, ktoré priniesol.
- Pomocný text prepínača *Spôsob A evidencie zásob* uvádza, že priebežná
  evidencia je povinná pre auditované firmy; tento návod to nepotvrdzuje.
