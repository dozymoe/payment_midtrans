# -*- coding: utf-8 -*-

import json
import logging
from odoo import api, fields, models
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.http import request
#from odoo.addons.payment_midtrans.controllers.main import MidtransController
from odoo.tools.float_utils import float_compare
import requests
import urlparse
from dateutil.parser import parse as dateparse
import pytz


_logger = logging.getLogger(__name__)


class AcquirerMidtrans(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('midtrans', 'Midtrans')])
    midtrans_method = fields.Selection([
            ('snap', 'SNAP'),
            ('core', 'Core API')],
            string='Midtrans Method')

    midtrans_merchant_id = fields.Char('Midtrans Merchant ID',
            required_if_provider='midtrans', groups='base.group_user')
    
    midtrans_client_key = fields.Char('Midtrans Client Key',
            required_if_provider='midtrans', groups='base.group_user')

    midtrans_server_key = fields.Char('Midtrans Server Key',
            required_if_provider='midtrans', groups='base.group_user')


    @api.multi
    def midtrans_form_generate_values(self, values):
        values['client_key'] = self.midtrans_client_key
        if self.environment == 'test':
            values['snap_js_url'] = 'https://app.sandbox.midtrans.com/snap/snap.js'
        else:
            values['snap_js_url'] = 'https://app.midtrans.com/snap/snap.js'

        return values


    def get_backend_endpoint(self):
        if self.environment == 'test':
            return 'https://app.sandbox.midtrans.com/snap/v1/transactions'

        return 'https://app.midtrans.com/snap/v1/transactions'
