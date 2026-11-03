---
title: MIS Builder – ikona poznámky
summary: Poznámka k buňce výkazu MIS Builder se přidává přes ikonu poznámky místo rozbalovací šipky, která vypadala, jako by šel řádek rozbalit.
verified: 19.0.1.0.0
---

## K čemu slouží {#purpose}

[module:mis_builder](module:mis_builder) umožňuje připojit k buňce výkazu
poznámku. Nabízel to přes rozbalovací šipku v každé buňce, která otevřela
nabídku s jedinou položkou *Annotate*. Šipka dolů působí jako „tento řádek
jde rozbalit“, což mate vedle řádků, které se opravdu rozbalují, a šedou
šipku měly i buňky, ke kterým poznámku přidat nelze.

Modul šipku nahrazuje ikonou poznámky. Nic se nenastavuje: nainstaluje se
spolu s `mis_builder` a nic jiného nemění.

## Jak se chová {#behaviour}

- Když ukážete na řádek, u každé hodnoty, ke které lze přidat poznámku, se
  objeví prázdná ikona; kliknutím poznámku napíšete. Dialog je stejný jako
  dosud.
- Buňka s poznámkou má ikonu vyplněnou a viditelnou stále, vedle čísla
  poznámky. Kliknutím poznámku změníte; samotná poznámka je pod výkazem, kde
  ji lze i smazat.
- Buňky, ke kterým poznámku přidat nelze (například řádky detailů), ikonu
  nemají.
- Ikonu vidí jen uživatelé, kteří mohou poznámky upravovat.
