---
title: Bank Feeds — Journal Header
summary: One header on the bank journal form where every bank feed puts its actions.
verified: 19.0.1.0.0
---

Odoo's bank journal form has no header bar, so each bank feed used to put its buttons somewhere in the body of the form, the Tatra banka ones even inside their own tab. This module adds one header bar to the form of every bank journal, and the bank feed modules (Tatra banka Premium API, Fio banka) show their actions there: *Pull transactions*, *Pull a range…*, *Re-read from the bank* and the like. Each button appears only when its feed is the journal's *Bank Feeds* setting.

It has no screen and no settings of its own. It is installed as a dependency of the bank feed modules.
