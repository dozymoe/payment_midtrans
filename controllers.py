import json
import logging
from odoo.exceptions import ValidationError
from odoo import http
from odoo.http import request
from odoo.tools import html_escape
import requests

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

        amount = post.get('amount')
        if not amount:
            raise ValidationError('amount is required.')

        try:
            amount = int(amount)
        except (ValueError, TypeError):
            raise ValidationError('Invalid amount.')

        currency_id = post.get('currency_id')
        if not currency_id:
            raise ValidationError('currency_id is required.')

        try:
            currency_id = int(currency_id)
        except (ValueError, TypeError):
            raise ValidationError('Invalid currency_id.')

        acquirer = request.env['payment.acquirer'].browse(acquirer_id)
        currency = request.env['res.currency'].browse(currency_id)
        order = request.website.sale_get_order()

        response = {
            'acquirer_id': acquirer_id,
            'order_id': order.id,
            'order_reference': order.name,
            'amount': amount,
            'currency_id': currency_id,
        }

        headers = {
            'accept': 'application/json',
        }
        payload = {
            'transaction_details': {
                'order_id': order.name,
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
        # transaction_details.order_id in Midtrans request/response is
        # order.name or payment.transaction.reference
        logger.error(repr(post))
        print(repr(post))
        order_id = post.get('order_id')
        if not order_id:
            raise ValidationError('order_id is required.')

        status = post.get('transaction_status')
        if not status:
            raise ValidationError('transaction_status is required.')

        tx = request.env['payment.transaction'].search([('reference', '=',
                order_id)])

        tx.write({'state': status})


    @http.route('/midtrans/notification', auth='public', methods=('post',), csrf=False, type='json')
    def midtrans_notification(self, **post):
        logger.error(repr(post))
        print(repr(post))


    @http.route('/midtrans/callback', auth='public', methods=('post',), csrf=False, type='json')
    def midtrans_callback(self, **post):
        logger.error(repr(post))
        print(repr(post))
