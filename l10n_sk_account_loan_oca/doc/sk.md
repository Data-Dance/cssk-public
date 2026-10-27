---
title: SK lízing — nástroj Community (OCA)
summary: Každý nový úver alebo lízing OCA otvorí so slovenskými účtami a pri lízingu, ktorý je dodaním tovaru, nechá faktúry za splátky bez DPH.
verified: 19.0.1.2.0
family: l10n_sk_account_loan_base#community
---

Vyplní nový úver alebo lízing nástroja OCA slovenskými účtami z nastavení spoločnosti — *Long term account* 474000, *Short term account* 474100, *Interests account* 562000 a účet prenajatého majetku 022000 — a pri zmene spoločnosti na formulári ich doplní znova. Pri spoločnostiach so slovenskou osnovou pribudne na karte *Leasing* slovenský daňový režim: *Režim DPH*, odpisová skupina a upozornenie na 60 % dobu nájmu. Ak je režimom dodanie tovaru, modul odstráni DPH z faktúr za splátky, ktoré nástroj vytvára, pretože taký prenájom sa zdaňuje raz pri odovzdaní; kým režim nie je zvolený, splátky si DPH ponechajú. Podrobnosti opisuje úplný návod.

Nainštaluje sa sám, keď je nainštalovaný [module:l10n_sk_account_loan_base](module:l10n_sk_account_loan_base) aj OCA `account_leasing`, a nemožno ho nainštalovať spolu s úvermi Enterprise (`account_loans`).
