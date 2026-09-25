Per employee/contract (under the *Payroll* access group):

* **Tax Declaration Signed (Vyhlásenie)** — enables the monthly non-taxable
  part (NČZD) and the child tax bonus for this employer.
* **Children < 15y** / **Children 15–17y** — counts for the child tax bonus
  (daňový bonus na dieťa).
* **ZŤP / Disabled** — applies the halved health-insurance rate.
* **Meal Allowance Type** and **Meal Days / Month** — drive the meal allowance;
  optional per-day overrides are available.

The statutory rates and ceilings are maintained as dated values under
*Payroll → Configuration → Rule Parameters*; add a new dated value to roll a
figure forward to a new year.

**Annual leave (dovolenka) accrual plans.** Three statutory accrual plans are
installed and attached to the SK holiday leave type: *Základná dovolenka
4 týždne (20 dní)* (§103 ods. 1), *Dovolenka 5 týždňov (25 dní)* pre
zamestnanca, ktorý do konca roka dovŕši 33 rokov alebo sa trvale stará o dieťa
(§103 ods. 2), and *Dovolenka 8 týždňov (40 dní)* pre pedagogických/výskumných
zamestnancov (§103 ods. 3; Zákonník práce, zák. č. 311/2001 Z. z.). Each plan
accrues in DAYS at 1/12 of the annual entitlement per whole calendar month
(§101), so a partial year yields the pomerná časť automatically, with the annual
figure capped per year. Assign the right plan to each employee with an accrual
allocation (*Time Off → Allocations*). The 5-week / 8-week eligibility
(dovŕšenie 33 rokov / trvalá starostlivosť o dieťa / pedagogický zamestnanec)
is a legal fact that cannot be derived from payroll data and must be chosen
manually. The special §105 "dovolenka za odpracované dni" (1/12 per 21 worked
days when fewer than 60 days are worked) is not modelled automatically.
