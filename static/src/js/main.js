odoo.define('payment.acquirer.midtrans', function(require)
{
    "use strict";

    var session = require('web.session');

    function set_state_busy($el, is_busy)
    {
        var $spin = $el.find('i.fa-spinner');
        if (is_busy)
        {
            $el.attr('disabled', 'disabled');
            $spin.removeClass('hidden');
        }
        else
        {
            $el.removeAttr('disabled');
            $spin.addClass('hidden');
        }
    }

    function attach_event_listener(selector)
    {
        var $btn = $(selector),
            $acquirer = $btn.closest('div.oe_sale_acquirer_button,div.oe_quote_acquirer_button,div.o_website_payment_new_payment'),
            acquirer_id = $acquirer.data('id') || $acquirer.data('acquirer_id');

        if (!acquirer_id)
        {
            alert('payment_midtrans got invalid acquirer_id');
            return;
        }

        $btn.on('click', function(event)
        {
            event.preventDefault();
            event.stopPropagation();
            set_state_busy($btn, true);
            
            var formData = $btn.parents('form').serializeArray().reduce(
                    function(m,e){m[e.name] = e.value; return m;}, {});

            formData['acquirer_id'] = acquirer_id
            formData['amount'] = parseFloat(formData['amount'])

            session.rpc('/midtrans/get_token', formData).then(function(response)
            {
                if (response.snap_errors)
                {
                    alert(response.snap_errors.join('\n'));
                    set_state_busy($btn, false);
                    return;
                }

                // order_reference in response is order_id in midtrans's reply
                // order_id in response is primary key of model sale.order
                console.log(response);

                var promise;

                if ($('.o_website_payment').length !== 0)
                {
                    promise = session.rpc('/website_payment/transaction', {
                        reference: response.order_reference,
                        amount: response.amount,
                        currency_id: response.currency_id,
                        acquirer_id: response.acquirer_id,

                    });
                }
                else
                {
                    promise = session.rpc('/shop/payment/transaction/' +
                            response.acquirer_id, {

                        so_id: response.order_id,

                    }, {'async': false});
                }

                promise.then(function()
                {
                    console.log(arguments);

                    snap.pay(response.snap_token,
                    {
                        onSuccess: function(result)
                        {
                            session.rpc('/midtrans/validate', {
                                order_id: result.order_id,
                                transaction_status: 'done',

                            }).then(function()
                            {
                                window.location = '/shop/confirmation';
                            });
                        },
                        onPending: function(result)
                        {
                            session.rpc('/midtrans/validate', {
                                order_id: result.order_id,
                                transaction_status: 'pending',

                            }).then(function()
                            {
                                window.location = '/shop/confirmation';
                            });
                        },
                        onError: function(result)
                        {
                            session.rpc('/midtrans/validate', {
                                order_id: result.order_id,
                                transaction_status: 'error',

                            }).then(function()
                            {
                                window.location = '/shop/confirmation';
                            });
                        },
                    });
                }, function(error)
                {
                    set_state_busy($btn, false);
                    console.log(error);
                });
            }, function(error)
            {
                set_state_busy($btn, false);
                console.log(error);
            });
        });
    }

    odoo.payment_midtrans = {
        attach: attach_event_listener,
    };
});
