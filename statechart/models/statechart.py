# -*- coding: utf-8 -*-
# Copyright 2016 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import io
import json
import logging

from openerp import api, fields, models, _
from openerp import tools

from sismic.exceptions import StatechartError
from sismic import io as sismic_io

from .interpreter import Interpreter

_logger = logging.getLogger(__name__)


class Statechart(models.Model):

    _name = 'statechart'
    _description = 'Statechart'

    name = fields.Char(
        related='model_id.model',
        readonly=True)
    model_id = fields.Many2one(
        'ir.model',
        string='Model',
        required='True',
        ondelete='restrict')
    yaml = fields.Text(
        help="YAML representation of the state chart."
             "Currently it is the input, to become a computed field "
             "from a future record-based reprensentation of "
             "the statechart.")

    _sql_constraint = [
        ('unique_model_id',
         'unique(model_id)',
         u'There can be at most one statechart per model')
    ]

    @api.multi
    def get_statechart(self):
        self.ensure_one()
        _logger.debug("loading statechart model for %s", self.display_name)
        with io.StringIO(self.yaml) as f:
            try:
                return sismic_io.import_from_yaml(f)
            except StatechartError:
                # TODO better error message
                raise

    @api.model
    @tools.ormcache('record')
    def interpreter_for(self, record):
        _logger.debug("initializing interpreter for %s", record)
        record.ensure_one()
        statechart = self.statechart_for_model(record._model._name)
        initial_context = {
            'o': record,
            # TODO: more action context
        }
        interpreter = Interpreter(
            statechart, initial_context=initial_context)
        if record.sc_state:
            config = json.loads(record.sc_state)
            interpreter.restore_configuration(config)
        else:
            interpreter.execute_once()
        return interpreter

    @api.model
    @tools.ormcache('model_name')
    def statechart_for_model(self, model_name):
        """Load and parse the statechart for an Odoo model."""
        statechart = self.search([('model_id.model', '=', model_name)])
        if not statechart:
            return
        return statechart.get_statechart()

    @api.multi
    def write(self, vals):
        self.statechart_for_model.clear_cache(self)
        self.interpreter_for.clear_cache(self)
        return super(Statechart, self).write(vals)

    @api.multi
    def unlink(self):
        self.statechart_for_model.clear_cache(self)
        self.interpreter_for.clear_cache(self)
        return super(Statechart, self).unlink()
