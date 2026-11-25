---
title: Česká účetní lokalizace — kompletní sada
summary: Nainstaluje českou zákonnou lokalizaci jedním krokem, volitelné části nabídne jako přepínače v nastavení a porovná podání k DPH mezi sebou a s účetnictvím.
verified: 19.0.1.4.0
---

## K čemu slouží {#purpose}

Česká lokalizace je rozdělená do mnoha modulů, aby si každá společnost
nainstalovala jen to, co potřebuje. Tento modul je cesta jedním kliknutím:
jeho instalace přinese zákonné jádro pro českou společnost a přidá přepínače
pro volitelné části. Přidává také tři **kontroly** mezi podáními k DPH
a účetnictvím (viz [níže](#reconciliation)).

## Co nainstaluje {#contents}

| Oblast | Modul |
|---|---|
| Společné jádro: nastavení, finanční úřady, životní cyklus podání | [module:l10n_cssk_core](module:l10n_cssk_core) |
| Česká zákonná báze | [module:l10n_cz_statutory](module:l10n_cz_statutory) |
| Přiznání k DPH (DPHDP3) | [module:l10n_cz_vat_return](module:l10n_cz_vat_return) |
| Kontrolní hlášení (DPHKH1) | [module:l10n_cz_kh](module:l10n_cz_kh) |
| Souhrnné hlášení (DPHSHV) | [module:l10n_cz_ec_sales](module:l10n_cz_ec_sales) |
| Česká faktura | [module:l10n_cz_invoice](module:l10n_cz_invoice) |
| Saldokonto a zápočty | [module:l10n_cssk_partner_balances](module:l10n_cssk_partner_balances) |
| Ověření DIČ v systému VIES | [module:l10n_cssk_vies](module:l10n_cssk_vies) |
| Dohadné položky | [module:l10n_cssk_accrual](module:l10n_cssk_accrual) |
| Inventarizace (inventurní soupisy) | [module:l10n_cz_inventory_verification](module:l10n_cz_inventory_verification) |

Každý z těchto modulů má vlastní návod.

## Volitelné části {#setup}

*Účetnictví → Konfigurace → Nastavení*, blok **Česká / slovenská
lokalizace**. Zaškrtněte přepínač a uložte: Odoo modul nainstaluje.
Odškrtnutím ho zase odinstaluje.

| Přepínač | Nainstaluje | Poznámka |
|---|---|---|
| Synchronizace kurzů (ČNB) | [module:currency_rate_update_cz](module:currency_rate_update_cz) | denní kurzy České národní banky; jen Community |
| Časové rozlišení | [module:l10n_cz_account_cutoff](module:l10n_cz_account_cutoff) | náklady a výnosy příštích období (381–385); jen Community |
| Kontrola spolehlivosti dodavatele | [module:l10n_cz_payment_reliability](module:l10n_cz_payment_reliability) | před platbou ověří nespolehlivého plátce a zveřejněný bankovní účet |
| Dvojí odpisování | [module:l10n_cz_account_asset_tax](module:l10n_cz_account_asset_tax) | daňové odpisy vedle účetních |
| Způsob A evidence zásob | `l10n_cz_stock_account_method_a` | průběžné účtování zásob způsobem A; dodává se v samostatném repozitáři |
| Zálohové faktury | [module:l10n_cz_sale_order_advance_invoice](module:l10n_cz_sale_order_advance_invoice) | zálohové faktury a daňové doklady k přijaté platbě |
| *Účetní vzory (interní doklady)* | [module:l10n_cz_account_move_template](module:l10n_cz_account_move_template) | pojmenované vzory MD/D pro interní doklady |
| *Účetní závěrka* | [module:l10n_cz_fiscal_year_closing](module:l10n_cz_fiscal_year_closing) | uzavření roku přes 710 / 702, otevření přes 701 s výsledkem hospodaření na 431 |
| *Protokoly k majetku* | [module:l10n_cz_asset_protocol_oca](module:l10n_cz_asset_protocol_oca) | protokoly o zařazení a vyřazení dlouhodobého majetku |
| *Manažerské výkazy* | [module:l10n_cz_mis_reports](module:l10n_cz_mis_reports) | manažerská výsledovka na MIS Builderu; není to zákonný výkaz |
| *Vytěžování faktur (AI)* | `account_invoice_ai_extract` | načte přijaté faktury z PDF; dodává se předplatitelům |
| *Účetní závěrka (Rozvaha, VZZ)* | [module:l10n_cz_fs](module:l10n_cz_fs) | rozvaha a výkaz zisku a ztráty |
| *Přiznání k dani z příjmů (DPPDP9)* | [module:l10n_cz_dppo](module:l10n_cz_dppo) | přiznání k dani z příjmů právnických osob |

V Odoo Enterprise jsou přepínače kurzů a časového rozlišení skryté, protože
Enterprise má vlastní automatické kurzy i časové rozlišení nákladů a výnosů.

## Kontroly mezi podáními {#reconciliation}

Před podáním porovnají tři tlačítka podání k DPH české společnosti mezi
sebou a s účetnictvím. Každé otevře obrazovku porovnání z modulu
[module:l10n_cssk_core](module:l10n_cssk_core), kde si každý řádek drží
částky, stav i vaši poznámku i po dalším spuštění.

| Kde | Tlačítko | Co se porovnává |
|---|---|---|
| Kontrolní hlášení | *Porovnat s přiznáním* | osm kontrolních řádků hlášení s řádky přiznání |
| Souhrnné hlášení | *Porovnat s přiznáním* | hlášení podle kódů s ř. 20, 21 a 31 |
| Přiznání k DPH | *Porovnat s účetnictvím* | daň z přiznání s účtem 343 |

Tlačítka se objeví po výpočtu podání. První dvě potřebují vypočtené přiznání
za stejné období.

**Kontrolní hlášení ↔ přiznání.** Hlášení končí kontrolními řádky
a struktura Finanční správy uvádí, kterému řádku přiznání má každý odpovídat
s tolerancí 1 000 Kč:

| Kontrolní řádek | Kontrolní hlášení | Přiznání |
|---|---|---|
| obrat23 / obrat5 | základy A.4 + A.5, základní / snížená sazba | ř. 1 / ř. 2 |
| pln23 / pln5 | základy B.2 + B.3, základní / snížená sazba | ř. 40 / ř. 41 |
| pln_rez_pren | základ A.1 | ř. 25 |
| rez_pren23 / rez_pren5 | základy B.1, základní / snížená sazba | ř. 10 / ř. 11 |
| celk_zd_a2 | základy A.2 | ř. 3 + 4 + 5 + 6 + 9 + 12 + 13 |

Rozdíl nad 1 000 Kč se hlásí jako rozdíl.

**Souhrnné hlášení ↔ přiznání.** Pokyny k přiznání posílají do souhrnného
hlášení tři řádky: ř. 20 s kódy 0 a 1 (dodání zboží a přemístění obchodního
majetku), ř. 21 s kódem 3 (služby podle § 9 odst. 1) a ř. 31 s kódem 2
(prostřední osoba třístranného obchodu).

**Čtvrtletní plátci.** Je-li přiznání čtvrtletní a hlášení měsíční, sečtou
se před porovnáním hlášení všech tří měsíců. Není-li některé vypočteno,
řádky se zobrazí jako *informativní* s poznámkou, ne jako rozdíly.

**Přiznání ↔ účetnictví.**

| Řádek | Přiznání | Účetnictví |
|---|---|---|
| Daň na výstupu | ř. 62 | daň na výstupu zaúčtovaná na 343 daňovými řádky, včetně daně přiznané příjemcem (přenesení daňové povinnosti, pořízení z EU) |
| Odpočet daně | ř. 46, oba sloupce | odpočet zaúčtovaný na 343 daňovými řádky |
| Pohyby na účtu 343 mimo daňové řádky | — | co se na 343 pohnulo bez daně: platby správci daně a od něj a vše zaúčtované ručně |
| Uskutečněná plnění ↔ tržby | ř. 1, 2, 20–26 | obrat strany Dal účtové skupiny 60; jen pro orientaci |

První dva řádky musí souhlasit s tolerancí 20 Kč (každý řádek přiznání se
zaokrouhluje na celé koruny samostatně). Poslední dva jsou informativní:
třetí si prohlédněte, pokud ho nevysvětlují platby daně.

## Omezení {#limitations}

- Kontroly jsou jen upozornění. Export ani podání neblokují.
- Kontroly čtou to, co je vypočteno v Odoo. Podání učiněné jinde nevidí
  a kontrola účetnictví čte účet 343 podle jeho čísla.
- Řádky přiznání s koeficientem (52, 53, 60) se s účetnictvím neporovnávají;
  žádný daňový řádek je neúčtuje.
- Přepínač modulu, který na serveru není (způsob A, účetní závěrka a přiznání
  k dani z příjmů se dodávají samostatně), nedělá nic.
- Odinstalace tohoto modulu neodinstaluje moduly, které přinesl.
- Nápověda k přepínači *Způsob A evidence zásob* uvádí, že průběžná evidence je
  povinná pro auditované firmy; tento návod to nepotvrzuje.
