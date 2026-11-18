"""Prueba transaccional de permisos y aprobación; revierte todos los datos."""
from odoo.exceptions import AccessError, ValidationError

assert env.cr.dbname == 'wheelwright_ahorra_dev'

def denied(operation, exception=AccessError):
    try:
        with env.cr.savepoint():
            operation()
    except exception:
        return
    raise AssertionError('La operación debió ser rechazada')

try:
    portal = env.ref('base.group_portal')
    users = env['res.users'].sudo().with_context(no_reset_password=True, tracking_disable=True).create([
        {'name': f'PRUEBA COMERCIANTE {n}', 'login': f'prueba-comercio-{n}@example.invalid',
         'group_ids': [(6, 0, portal.ids)]} for n in [1, 2]
    ])
    stores = []
    for n, user in enumerate(users, 1):
        store = env['wah.merchant'].with_user(user).create({
            'name': f'LOCAL PRUEBA {n}', 'street': 'Domicilio ficticio - no operar',
            'phone': '0000000000', 'category_id': 9,
        })
        assert store.owner_id == user and store.state == 'pending'
        stores.append(store)
    assert env['wah.merchant'].with_user(users[0]).search([]).ids == stores[0].ids
    denied(lambda: stores[1].with_user(users[0]).read(['name']))
    denied(lambda: stores[0].write({'owner_id': users[1].id}))
    denied(lambda: stores[0].action_approve())
    print('PASS: cada comerciante ve solo su local y no puede cambiar dueño ni aprobarlo')

    vals = {'merchant_id': stores[0].id, 'name': 'Producto de prueba', 'presentation': 'unidad',
            'category_id': 9, 'price': 121, 'image': env['product.template'].browse(59).image_128}
    denied(lambda: env['wah.merchant.product'].with_user(users[0]).create(vals.copy()), ValidationError)
    for store in stores:
        store.sudo().action_approve()
    product = env['wah.merchant.product'].with_user(users[0]).create(vals.copy())
    denied(lambda: env['wah.merchant.product'].with_user(users[1]).create(vals.copy()))
    denied(lambda: product.with_user(users[1]).read(['name']))
    denied(lambda: product.write({'merchant_id': stores[1].id}))
    denied(lambda: product.write({'state': 'approved'}))
    denied(lambda: product.action_approve())
    denied(lambda: env['product.template'].with_user(users[0]).create({'name':'No autorizado'}))
    denied(lambda: product.write({'price': 0}), ValidationError)
    print('PASS: no puede cargar para otro local ni publicar o aprobar productos directamente')

    product.action_submit()
    assert product.state == 'pending'
    product.sudo().action_approve()
    actual = product.sudo().product_tmpl_id
    assert actual.is_published and actual.wah_store_id == stores[0].sudo().partner_id
    gross = actual.taxes_id.compute_all(actual.list_price, currency=actual.currency_id,
                                       product=actual.product_variant_id)['total_included']
    assert actual.currency_id.compare_amounts(gross, 121) == 0, (actual.list_price, gross)
    print('PASS: aprobación publica en el local correcto y conserva el precio final con impuestos')

    product.write({'name': 'Producto modificado'})
    assert product.state == 'draft' and not actual.is_published
    product.action_submit()
    product.sudo().action_approve()
    assert actual.is_published
    stores[0].sudo().action_reject()
    assert not actual.is_published and product.state == 'rejected'
    print('PASS: editar requiere revisión; suspender el local retira sus productos')
finally:
    env.cr.rollback()
    print('Datos ficticios revertidos: sin cuentas ni productos de prueba guardados.')
