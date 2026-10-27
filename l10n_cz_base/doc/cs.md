---
title: Česká základní lokalizace (čísla bankovních účtů)
summary: Zobrazí český IBAN v národním formátu — předčíslí, číslo účtu a kód banky — a převádí mezi oběma tvary pro moduly, které to potřebují.
verified: 19.0.2.0.3
---

## K čemu slouží {#purpose}

Český bankovní účet se zapisuje dvojím způsobem: jako **IBAN**
(`CZ65 0800 0000 1920 0014 5399`) a v **národním formátu**
`19-2000145399/0800` — nepovinné předčíslí, číslo účtu a čtyřmístný kód
banky. Tuzemští obchodní partneři, bankovní soubory i doklady jako ISDOC
národní formát stále používají.

Odoo ukládá jedno číslo účtu. Modul jím ponechává IBAN a části národního
formátu z něj odvozuje, takže jsou k dispozici oba tvary. Jde o stavební
kámen: [module:account_edi_isdoc](module:account_edi_isdoc) z něj čte a do něj
zapisuje národní formát a jiné moduly používají jeho převod.

Navíc ještě jednu verzi drží staré názvy polí platebních symbolů (viz
[Platební symboly](#symbols)).

## Právní rámec {#legal}

Strukturu čísla účtu stanoví [vyhláška ČNB č. 169/2011 Sb.](law:cz/2011/169):
IBAN má 24 znaků — `CZ`, dvě kontrolní číslice, čtyřmístný kód platebního
styku (§ 6) a šestnáctimístný identifikátor účtu klienta (§ 5), který se
skládá z první části (předčíslí) o nejvýše 6 číslicích a druhé části o 2 až
10 číslicích, přičemž úvodní nuly jsou bez významu (§ 4, § 5).

## Bankovní účty {#bank-accounts}

Na bankovním účtu (*Kontakty → kontakt → karta Fakturace → Bankovní účty*
nebo *Účetnictví → Konfigurace → Bankovní účty*) se za polem *Číslo účtu*
zobrazí tři pole jen pro čtení:

| Pole | Příklad | Obsah |
|---|---|---|
| Kód banky | `0800` | 5. až 8. znak IBAN |
| Předčíslí účtu ve starém formátu | `000019` | 9. až 14. znak |
| Číslo účtu ve starém formátu | `2000145399` | 15. až 24. znak |

Jako číslo účtu zadejte **IBAN**; tři pole se vyplní při uložení. Jsou
vypočtená a nelze je upravit. U účtu, který není českým IBAN, zůstanou
prázdná.

## Převod pro jiné moduly {#conversion}

Moduly, které si vyměňují doklady s tuzemskými systémy, používají převod
oběma směry:

- národní formát uloženého účtu: `19-2000145399` a kód banky `0800`, bez
  úvodních nul;
- IBAN z čísla v národním formátu, které přišlo v doručeném dokladu
  (`19-2000145399/0800`), včetně výpočtu kontrolních číslic, takže účet lze
  dohledat nebo založit ve tvaru IBAN.

I účet zadaný v národním formátu místo IBAN tento převod pochopí: IBAN se z
něj dopočítá.

## Platební symboly {#symbols}

Variabilní, konstantní a specifický symbol poskytuje modul
[module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols), který
se s tímto modulem nainstaluje. Starší verze tohoto modulu měly vlastní pole
symbolů; při aktualizaci se sloučila se společnými a staré technické názvy
(`variable_symbol`, `constant_symbol`, `specific_symbol`) zůstávají ještě
jednu verzi jako aliasy společných polí, aby starší integrace dál fungovaly.
Není tu co nastavovat; řiďte se návodem k platebním symbolům.

## Omezení {#limitations}

- Části národního formátu se odvozují jen z IBAN. Je-li číslo účtu zadáno v
  národním formátu, tři pole zůstanou prázdná (jiné moduly ho přesto převést
  umí, viz výše).
- Číslo účtu se nekontroluje váženým algoritmem ČNB (příloha vyhlášky
  č. 169/2011 Sb.) ani proti číselníku kódů bank; IBAN se ověřuje jen v
  rozsahu, v jakém IBAN ověřuje samo Odoo.
- Předčíslí se v poli zobrazuje s úvodními nulami (`000019`), v převedeném
  výstupu bez nich.
- Staré názvy polí symbolů budou odstraněny; integrace by měly přejít na pole
  `l10n_cssk_*`.
