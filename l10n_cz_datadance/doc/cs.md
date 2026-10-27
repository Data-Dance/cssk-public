---
title: Česká účetní lokalizace — kompletní sada
summary: Nainstaluje českou zákonnou lokalizaci jedním krokem a volitelné části nabídne jako přepínače v nastavení.
verified: 19.0.1.1.1
---

## K čemu slouží {#purpose}

Česká lokalizace je rozdělená do mnoha modulů, aby si každá společnost
nainstalovala jen to, co potřebuje. Tento modul je cesta jedním kliknutím:
jeho instalace přinese zákonné jádro pro českou společnost a přidá přepínače
pro volitelné části. Vlastní obrazovky ani data nemá.

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
| *Účetní závěrka (Rozvaha, VZZ)* | [module:l10n_cz_fs](module:l10n_cz_fs) | rozvaha a výkaz zisku a ztráty |
| *Přiznání k dani z příjmů (DPPDP9)* | [module:l10n_cz_dppo](module:l10n_cz_dppo) | přiznání k dani z příjmů právnických osob |

V Odoo Enterprise jsou přepínače kurzů a časového rozlišení skryté, protože
Enterprise má vlastní automatické kurzy i časové rozlišení nákladů a výnosů.

## Omezení {#limitations}

- Přepínač modulu, který na serveru není (způsob A, účetní závěrka a přiznání
  k dani z příjmů se dodávají samostatně), nedělá nic.
- Odinstalace tohoto modulu neodinstaluje moduly, které přinesl.
- Nápověda k přepínači *Způsob A evidence zásob* uvádí, že průběžná evidence je
  povinná pro auditované firmy; tento návod to nepotvrzuje.
