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

    function get_form_data($el)
    {
        return $el.serializeArray().reduce(
                function(m,e){m[e.name] = e.value; return m;}, {});
    }

    function attach_event_listener(selector)
    {
        var $btn = $(selector),
            $form = $btn.parents('form'),
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
            
            var promise,
                formData = get_form_data($form);

            if ($('.o_website_payment').length !== 0)
            {
                promise = session.rpc(
                    '/website_payment/transaction',
                    {
                        reference: formData['reference'],
                        amount: formData['amount'],
                        currency_id: formData['currency_id'],
                        acquirer_id: acquirer_id,
                    })

                    .then(function()
                    {
                        return formData;
                    });
            }
            else
            {
                promise = session.rpc(
                    '/shop/payment/transaction/' + acquirer_id,
                    {
                        so_id: formData['order_id'],
                    },
                    {'async': false})

                    .then(function(html)
                    {
                        return get_form_data($(html));
                    });
            }

            promise
                .then(function(data)
                {
                    data['acquirer_id'] = acquirer_id;
                    return session.rpc('/midtrans/get_token', data);
                })
                .then(function(response)
                {
                    if (response.snap_errors)
                    {
                        alert(response.snap_errors.join('\n'));
                        set_state_busy($btn, false);
                        return;
                    }

                    snap.pay(response.snap_token,
                    {
                        onSuccess: function(result)
                        {
                            session.rpc('/midtrans/validate', {
                                reference: result.order_id,
                                transaction_status: 'done',
                                message: result.status_message,

                            }).then(function()
                            {
                                window.location = response.return_url;
                            });
                        },
                        onPending: function(result)
                        {
                            session.rpc('/midtrans/validate', {
                                reference: result.order_id,
                                transaction_status: 'pending',
                                message: result.status_message,

                            }).then(function()
                            {
                                window.location = response.return_url;
                            });
                        },
                        onError: function(result)
                        {
                            session.rpc('/midtrans/validate', {
                                reference: result.order_id,
                                transaction_status: 'error',
                                message: result.status_message,

                            }).then(function()
                            {
                                window.location = response.return_url;
                            });
                        },
                        onClose: function()
                        {
                            set_state_busy($btn, false);
                        },
                    });
                },
                function(error)
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
