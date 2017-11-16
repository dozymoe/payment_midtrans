import json
import logging
from odoo.exceptions import ValidationError
from odoo import http
from odoo.http import request
from odoo.tools import html_escape
import pprint
import requests
import werkzeug

logger = logging.getLogger(__name__)

def _prune_dict(data):
    if isinstance(data, dict):
        return {key: _prune_dict(value)\
                for key, value in data.items() if value is not None}

    return data


class MidtransController(http.Controller):

    @http.route('/midtrans/get_token', auth='public', type='json', website=True)
    def get_token(self, **post):
        acquirer_id = post.get('acquirer_id')
        if not acquirer_id:
            raise ValidationError('acquirer_id is required.')

        try:
            acquirer_id = int(acquirer_id)
        except (ValueError, TypeError):
            raise ValidationError('Invalid acquirer_id.')

        order_id = post.get('order_id')
        if not order_id:
            raise ValidationError('order_id is required.')

        try:
            order_id = int(order_id)
        except (ValueError, TypeError):
            raise ValidationError('Invalid order_id.')

        amount = post.get('amount')
        if not amount:
            raise ValidationError('amount is required.')

        try:
            amount = int(amount)
        except (ValueError, TypeError):
            raise ValidationError('Invalid amount.')

        reference = post.get('reference')
        if not reference:
            raise ValidationError('reference is required.')

        return_url = post.get('return_url')
        if not return_url:
            raise ValidationError('return_url is required.')

        acquirer = request.env['payment.acquirer'].browse(acquirer_id)
        order = request.env['sale.order'].browse(order_id)

        response = {
            'return_url': return_url,
        }

        headers = {
            'accept': 'application/json',
        }
        payload = {
            'transaction_details': {
                'order_id': reference,
                'gross_amount': amount,
            },
            'customer_details': {
                'first_name': post.get('partner_first_name'),
                'last_name': post.get('partner_last_name'),
                'email': post.get('partner_email'),
                'phone': post.get('partner_phone'),

                'billing_address': {
                    'first_name': post.get('billing_partner_first_name'),
                    'last_name': post.get('billing_partner_last_name'),
                    'email': post.get('billing_partner_email'),
                    'phone': post.get('billing_partner_phone'),
                    'address': post.get('billing_partner_address'),
                    'country_code': post.get('billing_partner_country_code'),
                    'postal_code': post.get('billing_partner_postal_code'),
                    'city': post.get('billing_partner_city'),
                },
            },
        }
        payload = _prune_dict(payload)
        resp = requests.post(acquirer.get_backend_endpoint(), json=payload,
                headers=headers, auth=(acquirer.midtrans_server_key, ''))

        if resp.status_code >= 200 and resp.status_code < 300:
            reply = resp.json()
            response['snap_token'] = reply['token']

        elif resp.text:
            reply = resp.json()
            if 'error_messages' in reply:
                response['snap_errors'] = resp.json().get('error_messages', [])

            else:
                _logger.warn('Unexpected Midtrans response: %i: %s',
                        resp.status_code, resp.text)
        else:
            response['snap_errors'] = ['Unknown error.']

        return response


    @http.route('/midtrans/validate', auth='public', type='json')
    def payment_validate(self, **post):
        reference = post.get('reference')
        if not reference:
            raise ValidationError('reference is required.')

        status = post.get('transaction_status')
        if not status:
            raise ValidationError('transaction_status is required.')

        message = post.get('message')
        if not message:
            raise ValidationError('message is required.')

        tx = request.env['payment.transaction'].search([('reference', '=',
                reference)], limit=1)

        tx.write({'state': status, 'state_message': message})

        order = tx.sale_order_id

        if status == 'done':
            order.write({'state': 'done'})
        elif status == 'pending':
            order.write({'state': 'sale'})


    @http.route('/midtrans/notification', auth='public', methods=('post',), csrf=False, type='json')
    def midtrans_notification(self, **post):
        logger.error(repr(post))
        print(repr(post))


    @http.route('/midtrans/callback', auth='public', methods=('post',), csrf=False, type='json')
    def midtrans_callback(self, **post):
        logger.error(repr(post))
        print(repr(post))
