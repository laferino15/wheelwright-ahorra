"""Prueba del flujo completo por comercio, sin guardar pedidos ni enviar correos."""
import secrets
from odoo.exceptions import AccessError, ValidationError

assert env.cr.dbname == 'wheelwright_ahorra_dev'

def denied(operation, exception=AccessError):
    try:
        with env.cr.savepoint():
            operation()
    except exception:
        return
    raise AssertionError('Se permitió una operación que debía rechazarse')

try:
    token = secrets.token_hex(4)
    users = env['res.users'].sudo().with_context(no_reset_password=True, tracking_disable=True).create([
        {'name': f'PRUEBA PREPARACION {i}', 'login': f'prep-{token}-{i}@example.invalid',
         'group_ids': [(6, 0, env.ref('base.group_portal').ids)]} for i in range(3)
    ])
    stores = env['wah.merchant'].sudo().create([
        {'name': f'LOCAL FICTICIO {i}', 'owner_id': users[i].id, 'category_id': 9, 'website_id': 1,
         'street': 'DOMICILIO DE PRUEBA', 'phone': '0000000000'} for i in range(2)
    ])
    stores.action_approve()
    products = env['product.template'].sudo().create([
        {'name': f'PRODUCTO LOCAL {i}', 'type': 'consu', 'wah_store_id': stores[i].partner_id.id,
         'list_price': 100, 'website_id': 1} for i in range(2)
    ])
    order = env['sale.order'].sudo().with_context(tracking_disable=True).create({
        'partner_id': users[2].partner_id.id, 'website_id': 1,
        'order_line': [(0, 0, {'product_id': product.product_variant_id.id,
                              'product_uom_qty': quantity, 'price_unit': product.list_price})
                       for product, quantity in [(products[0], 2), (products[1], 3), (env['product.template'].browse(59), 1)]],
    })
    assert not order.wah_preparation_ids
    assert order.order_line[0].wah_merchant_id == stores[0]
    # El dueño se conserva desde el carrito aunque cambie el producto del catálogo.
    products[0].wah_store_id = stores[1].partner_id
    order.with_context(send_email=False, mail_notrack=True, tracking_disable=True).action_confirm()
    preparations = order.wah_preparation_ids
    assert len(preparations) == 3 and order.wah_unassigned_count == 1
    order._ensure_wah_preparations()
    assert len(order.wah_preparation_ids) == 3
    a = preparations.filtered(lambda item: item.merchant_id == stores[0]).with_user(users[0])
    b = preparations.filtered(lambda item: item.merchant_id == stores[1]).with_user(users[1])
    unknown = preparations.filtered(lambda item: not item.merchant_id)
    assert a and b and a.line_ids.quantity == 2 and b.line_ids.quantity == 3
    print('PASS: confirmar distribuye cantidades por local; no duplica y conserva el dueño del carrito')

    assert env['wah.preparation'].with_user(users[0]).search([]).ids == a.ids
    denied(lambda: b.with_user(users[0]).read(['reference']))
    denied(lambda: b.line_ids.with_user(users[0]).read(['name']))
    denied(lambda: a.read(['order_id']))
    denied(lambda: a.write({'state': 'ready'}))
    denied(lambda: a.action_collect())
    denied(lambda: a.action_deliver())
    denied(lambda: env['wah.preparation'].with_user(users[0]).create({'name':'No autorizado'}))
    assert not env['wah.preparation'].with_user(users[2]).search([])
    assert order.with_user(users[2]).wah_preparation_state == 'received'
    print('PASS: local A no ve productos de B ni datos del pedido completo; comprador no accede al panel vendedor')

    denied(lambda: a.action_ready(), ValidationError)
    a.action_start(); assert a.state == 'preparing' and a.started_at
    a.action_save_note('PRUEBA: consultar antes de retirar')
    a.action_ready(); assert a.state == 'ready' and a.ready_at
    assert order.wah_preparation_state == 'preparing'
    b.action_start(); b.action_ready()
    unknown.action_start(); unknown.action_ready()
    assert order.wah_preparation_state == 'ready'
    denied(lambda: a.action_start(), ValidationError)
    denied(lambda: order.order_line[0].write({'product_uom_qty': 10}), ValidationError)
    preparations.action_collect(); assert order.wah_preparation_state == 'collected'
    preparations.action_deliver(); assert order.wah_preparation_state == 'delivered'
    assert not order.transaction_ids
    print('PASS: recibido -> preparación -> listo -> retiro -> entrega, sin registrar pagos')

    cancelled_order = env['sale.order'].sudo().with_context(tracking_disable=True).create({
        'partner_id': users[2].partner_id.id, 'website_id': 1,
        'order_line': [(0, 0, {'product_id': products[1].product_variant_id.id, 'product_uom_qty': 1})],
    })
    cancelled_order.with_context(send_email=False, tracking_disable=True).action_confirm()
    ticket = cancelled_order.wah_preparation_ids.with_user(users[1])
    ticket.action_start()
    cancelled_order.action_cancel()
    assert ticket.state == 'cancelled'
    denied(lambda: ticket.action_ready(), ValidationError)
    print('PASS: cancelar el pedido cancela la preparación y bloquea su avance')
finally:
    env.cr.rollback()
    print('Prueba revertida: no se guardaron usuarios, pedidos, retiros ni entregas ficticias.')
