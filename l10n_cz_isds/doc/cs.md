---
title: Datová schránka (ISDS)
summary: Přihlašuje se do datové schránky firmy přes webové služby provozovatele, aby z ní kanály pro podání mohly posílat datové zprávy a číst odpovědi, které přijdou zpět.
verified: 19.0.1.1.0
---

## K čemu slouží {#purpose}

Česká firma má **datovou schránku** (ISDS), státní kanál pro úřední zprávy.
Mnoho úřadů z ní přijímá podání: odesílatele určuje sama zpráva, takže
elektronický podpis není potřeba.

Modul propojí Odoo s datovou schránkou firmy přes webové služby provozovatele
(WSDL/XSD verze 3.11). Uchovává přihlašovací údaje a nabízí **Test
připojení**; kanály pro podání, které na něm stojí, posílají zprávy a čtou
odpovědi. Sám nic neposílá. Prvním, kdo ho využívá, je kanál pro podání JMHZ
na ČSSZ.

## Právní rámec {#legal}

Úkon, který firma učiní prostřednictvím datové schránky, má stejné účinky jako
úkon učiněný písemně a podepsaný ([§ 18 odst. 2 zákona č. 300/2008 Sb.](law:cz/2008/300)).
Proto podání datovou schránkou nepotřebuje kvalifikovaný certifikát.

## Nastavení {#setup}

Vidí jen uživatelé ve skupině **Zákonná podání: podávat**.

1. Zvolte, jak se Odoo přihlašuje:
   - **Jméno a heslo** — založte v datové schránce pro Odoo **uživatele**
     s právem posílat a číst zprávy. Samostatný uživatel je lepší než osobní
     přihlášení někoho z firmy: dá se odebrat samostatně a jeho heslo se
     nemění, když člověk odejde.
   - **Jméno, heslo a certifikát** — tentýž uživatel, jehož přihlášení navíc
     vyžaduje komerční certifikát, přiřazený mu v datové schránce.
   - **Systémový certifikát** (doporučeno pro server) — administrátor
     schránky v jejím nastavení zaregistruje **komerční certifikát** pro
     externí aplikaci. Odoo se pak přihlašuje jen certifikátem: žádné heslo,
     které by vypršelo nebo se měnilo, když někdo odejde.

   Certifikát musí vydat certifikační autorita, kterou provozovatel uznává
   (PostSignum, I.CA, eIdentity); jiný servery provozovatele odmítnou už při
   navazování zabezpečeného spojení.
2. *Nastavení → Uživatelé a společnosti → Společnosti*, firma, záložka
   **Datová schránka** (u českých firem):

| Pole | Účel |
|---|---|
| Prostředí datové schránky | *Test* (výchozí): testovací prostředí provozovatele (datovka-test.gov.cz) s testovacími schránkami a bez právních účinků. *Produkce*: skutečná schránka firmy (datovka.gov.cz). |
| Přihlášení do datové schránky | *Jméno a heslo*, *Jméno, heslo a certifikát* nebo *Systémový certifikát (bez hesla)*. |
| Přihlašovací jméno, heslo | Uživatel datové schránky, za kterého se Odoo přihlašuje (u systémového certifikátu se nepoužívá). |
| Certifikát datové schránky, heslo | Komerční certifikát se soukromým klíčem (`.p12` / `.pfx`) pro oba způsoby s certifikátem. Po uložení ho modul otevře a ukáže subjekt a platnost; soubor, který otevřít nejde, odmítne. |
| ID datové schránky, vlastník | Vyplní **Test připojení**. |

3. **Test připojení** se přihlásí a ukáže, čí schránku přihlašovací údaje
   otevírají. Nic neposílá.

Přihlašovací údaje i certifikát otevírají schránku komukoli, kdo je má, proto
heslo a certifikát může číst a měnit jen skupina, která smí podávat. Klíč
certifikátu se pro každé volání načte do zabezpečeného spojení z dočasného
souboru zašifrovaného jednorázovým heslem a smaže se dřív, než se cokoli
odešle.

## Omezení {#limitations}

- Přihlášení zabezpečené jednorázovým kódem (SMS, Mobilní klíč) software
  použít nemůže; použijte systémový certifikát. Přístup pro hostované
  spisové služby podporován není.
- Jen to, co potřebuje podání: odeslat zprávu, vypsat přijaté zprávy a jednu
  stáhnout. Zprávy se v Odoo nezobrazují jako schránka a nic se neoznačuje
  jako přečtené.
- Postaveno podle zveřejněných WSDL a XSD provozovatele (testy proti nim
  kontrolují každý požadavek); se skutečnou datovou schránkou zatím
  nevyzkoušeno.
