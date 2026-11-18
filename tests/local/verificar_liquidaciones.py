"""Liquidaciones con permisos reales y rollback de todos los datos ficticios."""
from datetime import timedelta
import secrets
from odoo.exceptions import AccessError, ValidationError

assert env.cr.dbname == 'wheelwright_ahorra_dev'

def denied(call, exception=ValidationError):
    try:
        with env.cr.savepoint():
            call()
    except exception:
        return
    raise AssertionError('La operación debía rechazarse')

try:
    token = secrets.token_hex(5)
    manager = env['res.users'].sudo().with_context(no_reset_password=True).create({
        'name': 'ADMIN LIQ FICTICIO', 'login': 'liq-admin-' + token + '@example.invalid',
        'group_ids': [(6, 0, [env.ref('base.group_user').id, env.ref('product.group_product_manager').id, env.ref('sales_team.group_sale_manager').id])]})
    owners = env['res.users'].sudo().with_context(no_reset_password=True).create([
        {'name': 'LOCAL LIQ FICTICIO', 'login': 'liq-' + token + str(i) + '@example.invalid',
         'group_ids': [(6, 0, env.ref('base.group_portal').ids)]} for i in range(2)])
    website = env['website'].browse(1)
    category = env['product.public.category'].search([('website_id', 'in', [False, website.id])], limit=1)
    merchants = env['wah.merchant'].sudo().create([
        {'name': 'LOCAL LIQ ' + str(i) + token, 'owner_id': owner.id, 'website_id': website.id,
         'category_id': category.id, 'street': 'FICTICIO', 'phone': '000000'} for i, owner in enumerate(owners)])
    merchants.action_approve()
    assert all(m.commission_rate == 0 for m in merchants)
    merchants[1].with_user(manager).write({'commission_rate': 12.5})
    denied(lambda: merchants[0].with_user(manager).write({'commission_rate': -1}))
    denied(lambda: merchants[0].with_user(manager).write({'commission_rate': 101}))
    denied(lambda: merchants[0].with_user(owners[0]).write({'commission_rate': 50}), AccessError)
    offers = env['wah.merchant.product'].sudo().create([
        {'merchant_id': m.id, 'name': 'PRODUCTO LIQ ' + token + str(i), 'presentation': 'unidad',
         'category_id': category.id, 'price': 100, 'image': env['product.template'].search([('image_1920', '!=', False)], limit=1).image_1920,
         'state': 'pending'} for i, m in enumerate(merchants)])
    offers.action_approve()
    date = env['sale.order']._wah_local_now().date() + timedelta(days=1)
    courier = env['wah.courier'].with_user(manager).create({'name': 'REPARTIDOR LIQ FICTICIO', 'phone': '000'})
    def make_order(deliver=True, collect=True):
        order = env['sale.order'].sudo().with_context(send_email=False, tracking_disable=True, mail_notrack=True).create({
            'partner_id': owners[0].partner_id.id, 'website_id': website.id,
            'wah_delivery_date': date, 'wah_delivery_window': 'midday',
            'order_line': [(0, 0, {'product_id': offer.product_tmpl_id.product_variant_id.id,
                'product_uom_qty': 1, 'price_unit': 100, 'tax_ids': [(5, 0, 0)]}) for offer in offers]
                + [(0, 0, {'product_id': offers[0].product_tmpl_id.product_variant_id.id,
                'name': 'ENVIO FICTICIO', 'is_delivery': True, 'product_uom_qty': 1, 'price_unit': 25, 'tax_ids': [(5, 0, 0)]})]})
        order.action_confirm()
        admin_order = order.with_user(manager)
        if deliver:
            admin_order.write({'wah_courier_id': courier.id})
            admin_order.action_wah_assign()
            for prep in order.wah_preparation_ids:
                prep.with_user(prep.merchant_id.owner_id).action_start()
                prep.with_user(prep.merchant_id.owner_id).action_ready()
                prep.with_user(manager).action_collect()
            admin_order.action_wah_dispatch()
            admin_order.action_wah_deliver()
            if collect:
                admin_order._wah_register_collection('cash', order.amount_total, order.amount_total, '')
        return order
    paid_order = make_order()
    unpaid_order = make_order(collect=False)
    pending_order = make_order(deliver=False)
    settlements = env['wah.settlement'].with_user(manager)
    def draft(merchant, start=date, end=date):
        return settlements.create({'merchant_id': merchant.id, 'date_from': start, 'date_to': end})
    denied(lambda: env['wah.settlement'].with_user(owners[0]).create({'merchant_id': merchants[0].id}), AccessError)
    denied(lambda: draft(merchants[0], date, date-timedelta(days=1)))
    empty = draft(merchants[0], date-timedelta(days=2), date-timedelta(days=1))
    denied(empty.action_generate)
    first = draft(merchants[0]); first.action_generate()
    assert first.gross_amount == 100 and first.net_amount == 100 and first.commission_amount == 0
    assert first.line_ids.order_id == paid_order and len(first.line_ids) == 1
    assert unpaid_order not in first.line_ids.order_id and pending_order not in first.line_ids.order_id
    print('PASS: comisión inicial 0 %, solo entregados y cobrados, envío excluido y filtro de período')
    duplicate = draft(merchants[0]); denied(duplicate.action_generate)
    denied(first.action_generate)
    denied(lambda: first.write({'state': 'paid'}), AccessError)
    denied(lambda: first.write({'date_to': date+timedelta(days=1)}), AccessError)
    denied(lambda: first.line_ids.with_user(manager).write({'net_amount': 1}), AccessError)
    denied(lambda: first.with_user(owners[0]).read(['net_amount']), AccessError)
    denied(lambda: first.with_user(owners[1]).action_confirm(), AccessError)
    denied(lambda: paid_order.wah_collection_ids.with_user(manager)._void('Corrección de prueba'))
    first.action_confirm(); denied(first.action_pay)
    first.write({'payment_method': 'transfer', 'payment_reference': 'TRANSFERENCIA FICTICIA VERIFICADA'})
    first.action_pay()
    assert first.state == 'paid' and first.paid_by == manager and first.paid_at
    denied(first.action_pay); denied(first.action_cancel)
    denied(lambda: first.write({'payment_reference': 'alterada'}), AccessError)
    denied(lambda: paid_order.wah_collection_ids.with_user(manager)._void('Corrección posterior al pago'))
    print('PASS: duplicados bloqueados, permisos, detalle inalterable, pago único con responsable y protección del cobro')
    second = draft(merchants[1]); second.action_generate()
    assert second.gross_amount == 100 and second.commission_amount == 12.5 and second.net_amount == 87.5
    merchants[1].with_user(manager).write({'commission_rate': 20})
    assert second.commission_amount == 12.5
    second.action_confirm(); denied(second.action_cancel)
    second.write({'cancel_reason': 'Corrección de comisión ficticia'}); second.action_cancel()
    assert second.state == 'cancelled' and second.line_ids.net_amount == 87.5 and not second.line_ids.reserved_preparation_id
    replacement = draft(merchants[1]); replacement.action_generate()
    assert replacement.net_amount == 80 and replacement.commission_amount == 20
    replacement.action_confirm()
    replacement.write({'payment_method': 'cash', 'payment_reference': 'RECIBO FICTICIO'})
    replacement.action_pay()
    assert first.gross_amount + replacement.gross_amount == 200
    assert first.net_amount + replacement.net_amount + replacement.commission_amount == 200
    print('PASS: comisión por local, snapshot, anulación con historial y nueva liquidación sin duplicar el pago')
    # Comprueba liberar el cobro cuando TODAS las liquidaciones del pedido se anulan.
    another = make_order()
    third = draft(merchants[0]); third.action_generate()
    denied(lambda: another.wah_collection_ids.with_user(manager)._void('Corrección ficticia'))
    third.write({'cancel_reason': 'Revisar cobro ficticio'}); third.action_cancel()
    another.wah_collection_ids.with_user(manager)._void('Corrección ficticia autorizada')
    assert another.wah_collection_state == 'pending'
    assert not env['wah.settlement.line'].sudo().search([('order_id', '=', another.id), ('reserved_preparation_id', '!=', False)])
    print('PASS: anular una liquidación sin pagar libera pedidos y permite corregir el cobro')
    assert not paid_order.invoice_ids and not paid_order.transaction_ids
    for view_name, view_type in [('settlement_form', 'form'), ('settlement_list', 'list'), ('settlement_search', 'search')]:
        result = settlements.get_view(env.ref('wheelwright_ahorra.' + view_name).id, view_type)
        assert result['arch']
    merchant_form = env['wah.merchant'].with_user(manager).get_view(env.ref('wheelwright_ahorra.merchant_form').id, 'form')
    assert 'commission_rate' in merchant_form['arch']
    other_company = env['res.company'].sudo().create({'name': 'COMPAÑIA FICTICIA LIQ ' + token})
    denied(lambda: first.with_context(allowed_company_ids=[other_company.id]).read(['net_amount']), AccessError)
    print('PASS: vistas administrativas válidas y aislamiento entre compañías')
    print('RESULTADO: LIQUIDACIONES APROBADAS')
finally:
    env.cr.rollback()
    print('Rollback completo: sin pagos, correos ni datos ficticios persistidos.')
