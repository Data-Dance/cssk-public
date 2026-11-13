-- Run by Odoo's database neutralization (odoo-bin neutralize, Odoo.sh staging
-- copies, duplicate-with-neutralize). A copy of production must never register
-- sales with the Financial Administration: switch EET 2.0 off on every company.
-- Certificates, EIC, unit ids and queued messages are kept, so the copy can be
-- re-enabled against the playground with a playground certificate.
UPDATE res_company
   SET l10n_cz_eet2_enabled = false
 WHERE l10n_cz_eet2_enabled;
