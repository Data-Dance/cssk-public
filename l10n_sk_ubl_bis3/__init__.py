# -*- coding: utf-8 -*-
from . import models


def uninstall_hook(env):
    # Scrub the SK format value from partners so the stored Selection stays valid.
    env["res.partner"]._clear_removed_edi_formats("ubl_bis3_sk")
