---
title: Czech Districts, Municipalities and Postcodes
summary: Every Czech okres, obec and PSČ, so that typing a postcode or a town on a contact fills in the town, the postcode, the district and the country.
verified: 19.0.1.0.0
---

## What it is for {#purpose}

The OCA module *Location management* (`base_location`) adds a **ZIP Location**
field to contacts and companies: type a postcode or the beginning of a town and
pick from the list, and the address is filled in for you. On its own it ships
no Czech data. This module adds it:

| In Odoo | In the Czech Republic | How many |
|---|---|---|
| State | okres, with its kraj ("okres Kladno, Středočeský kraj"); Prague is "Hlavní město Praha" | 77 |
| City | obec | 6,258 |
| ZIP | PSČ, as Česká pošta and ARES give it ("27201") | 7,871 |

Obce sharing a name are separate entries, each in its own okres (there are
fourteen called Nová Ves), so pick by the okres shown next to the name. Two
names occur twice within one okres, and those carry their postcode in brackets:
"Březina (66601)" and "Březina (67905)" in Brno-venkov, "Mezholezy (34506)"
and "Mezholezy (34601)" in Domažlice.

## Installing {#install}

It is not installed with the Czech localization package. Install it from
*Apps* when you want the postcode picker; it brings `base_location` with it.

## Where the data comes from {#source}

From Česká pošta's published list of obce and their parts with an address
postcode (*Seznam částí obcí a obcí s adresním PSČ*). The file `data/SOURCE` in
the module says which download it was built from. A newer release of the
module adds new obce and postcodes on update; it never removes or renames an
entry you may already use on a contact, and edits you make to the entries are
kept.
