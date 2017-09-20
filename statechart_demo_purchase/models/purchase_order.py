# -*- coding: utf-8 -*-
# Copyright 2016-2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, _
from openerp.exceptions import UserError


class PurchaseOrder(models.Model):

    _inherit = ['purchase.order', 'statechart.mixin']
    _name = 'purchase.order'

    def raise_user_error(self):
        raise UserError(_("Some error"))
