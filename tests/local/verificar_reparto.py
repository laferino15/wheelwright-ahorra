"""Circuito completo con permisos reales; todo se revierte al finalizar."""
from datetime import timedelta
import secrets
from odoo.exceptions import AccessError, ValidationError

assert env.cr.dbname=='wheelwright_ahorra_dev'
def denied(call, exception=ValidationError):
    try:
        with env.cr.savepoint():call()
    except exception:return
    raise AssertionError('La operación debía rechazarse')
try:
    token=secrets.token_hex(4)
    manager=env['res.users'].sudo().with_context(no_reset_password=True,tracking_disable=True).create({'name':'ADMIN FICTICIO REPARTO','login':f'admin-ruta-{token}@example.invalid','group_ids':[(6,0,[env.ref('base.group_user').id,env.ref('product.group_product_manager').id,env.ref('sales_team.group_sale_manager').id])]})
    users=env['res.users'].sudo().with_context(no_reset_password=True,tracking_disable=True).create([{'name':f'FICTICIO REPARTO {i}','login':f'ruta-{token}-{i}@example.invalid','group_ids':[(6,0,env.ref('base.group_portal').ids)]} for i in range(3)])
    users[2].partner_id.write({'street':'FICTICIO NO ENTREGAR','phone':'0000000'})
    stores=env['wah.merchant'].sudo().create([{'name':f'LOCAL RUTA {i}','owner_id':users[i].id,'website_id':1,'category_id':9,'street':'FICTICIO','phone':'000000'} for i in range(2)])
    stores.action_approve()
    offers=env['wah.merchant.product'].sudo().create([{'merchant_id':store.id,'name':f'PRODUCTO RUTA {i}','presentation':'unidad','category_id':9,'price':100,'image':env['product.template'].browse(59).image_1920,'state':'pending','stock_tracking':True,'stock_quantity':3} for i,store in enumerate(stores)])
    offers.action_approve()
    date=env['sale.order']._wah_local_now().date()+timedelta(days=1)
    order=env['sale.order'].sudo().with_context(send_email=False,tracking_disable=True,mail_notrack=True).create({'partner_id':users[2].partner_id.id,'website_id':1,'wah_delivery_date':date,'wah_delivery_window':'midday','order_line':[(0,0,{'product_id':offer.product_tmpl_id.product_variant_id.id,'product_uom_qty':1,'price_unit':100}) for offer in offers]})
    order.action_confirm()
    admin_order=order.with_user(manager).with_context(tracking_disable=True,send_email=False,mail_notrack=True)
    a=order.wah_preparation_ids.filtered(lambda prep:prep.merchant_id==stores[0]).with_user(users[0])
    b=order.wah_preparation_ids.filtered(lambda prep:prep.merchant_id==stores[1]).with_user(users[1])
    denied(admin_order.action_wah_assign)
    denied(lambda:order.with_user(users[2]).action_wah_dispatch(),AccessError)
    denied(lambda:a.action_collect(),AccessError)
    denied(lambda:admin_order.write({'wah_route_state':'delivered'}),AccessError)
    courier=env['wah.courier'].with_user(manager).create({'name':'REPARTIDOR FICTICIO','phone':'0000000'})
    admin_order.write({'wah_courier_id':courier.id});admin_order.action_wah_assign()
    denied(admin_order.action_wah_dispatch)
    denied(admin_order.action_wah_collection_wizard)
    a.action_start();a.action_ready();b.action_start();b.action_ready()
    a.with_user(manager).action_collect()
    denied(admin_order.action_wah_dispatch)
    denied(admin_order.action_cancel)
    b.with_user(manager).action_collect()
    assert admin_order.wah_route_state=='assigned'
    admin_order.action_wah_dispatch();admin_order.action_wah_dispatch()
    assert order.wah_route_state=='on_way' and order.wah_preparation_state=='on_way'
    assert order.with_user(users[2]).wah_preparation_state=='on_way'
    denied(lambda:admin_order.write({'wah_courier_id':False}))
    denied(lambda:admin_order.order_line[0].write({'price_unit':1}))
    denied(lambda:env['sale.order.line'].sudo().create({'order_id':order.id,'product_id':1,'product_uom_qty':1,'price_unit':1}))
    denied(lambda:a.with_user(manager).action_deliver())
    admin_order.action_wah_deliver();admin_order.action_wah_deliver()
    assert all(prep.state=='delivered' for prep in order.wah_preparation_ids)
    assert order.wah_collection_state=='pending' and not order.wah_collection_ids
    assert order.wah_dropoff_details and order.wah_departed_at and order.wah_delivered_at
    print('PASS: permisos, repartidor obligatorio, dos retiros, En camino y entrega sin cobro automático')
    total=order.amount_total
    denied(lambda:admin_order._wah_register_collection('cash',total,total-1,''))
    denied(lambda:admin_order._wah_register_collection('cash',total-1,total,''))
    denied(lambda:admin_order._wah_register_collection('cash',float('nan'),total,''))
    denied(lambda:admin_order._wah_register_collection('transfer',total,0,''))
    wizard=env['wah.collection.register'].with_user(manager).with_context(default_order_id=order.id).create({})
    wizard.write({'received_amount':total+50})
    wizard.action_register()
    receipt=order.wah_collection_ids
    assert len(receipt)==1 and receipt.amount==total and receipt.change_amount==50 and receipt.actor_id==manager and receipt.courier_id==courier
    assert order.wah_collection_state=='collected' and order.with_user(users[2]).wah_collection_state=='collected'
    denied(lambda:admin_order._wah_register_collection('cash',total,total,''))
    provider=env['payment.provider'].sudo().browse(25)
    if provider.exists() and provider.payment_method_ids:
        denied(lambda:env['payment.transaction'].sudo().create({'provider_id':provider.id,'payment_method_id':provider.payment_method_ids[0].id,'reference':'FICTICIO-DUPLICADO-'+token,'amount':total,'currency_id':order.currency_id.id,'partner_id':order.partner_id.id,'operation':'online_redirect','sale_order_ids':[(6,0,order.ids)]}))
    denied(lambda:receipt.with_user(manager).write({'amount':1}),AccessError)
    denied(lambda:receipt.with_user(users[2]).read(['amount']),AccessError)
    denied(lambda:order.with_user(users[2]).read(['wah_collection_ids']),AccessError)
    assert not order.transaction_ids
    print('PASS: cobro exacto, vuelto, responsable, anticobro duplicado y privacidad del registro')
    denied(lambda:receipt.with_user(manager)._void(''))
    void=env['wah.collection.void'].with_user(manager).create({'collection_id':receipt.id,'reason':'Corrección de prueba del medio de cobro'})
    void.action_void()
    assert receipt.state=='void' and receipt.voided_by==manager and order.wah_collection_state=='pending'
    replacement=admin_order._wah_register_collection('transfer',total,0,'TRANSFERENCIA FICTICIA VERIFICADA')
    assert replacement.state=='posted' and order.wah_collection_state=='collected' and len(order.wah_collection_ids)==2
    assert all(event.actor_id==manager for event in order.wah_route_event_ids)
    denied(lambda:order.wah_route_event_ids[:1].with_user(manager).write({'description':'alterado'}),AccessError)
    assert len(order.wah_route_event_ids)==8,len(order.wah_route_event_ids)
    assert all(offer.stock_quantity==2 for offer in offers)
    denied(admin_order.action_cancel)
    print('PASS: anulación con motivo y nuevo registro, historial inalterable y stock sin reposición después de entregar')
    cancelled=env['sale.order'].sudo().with_context(tracking_disable=True,send_email=False,mail_notrack=True,disable_cancel_warning=True).create({'partner_id':users[2].partner_id.id,'website_id':1,'wah_delivery_date':date,'wah_delivery_window':'afternoon','order_line':[(0,0,{'product_id':offers[0].product_tmpl_id.product_variant_id.id,'product_uom_qty':1,'price_unit':100})]})
    cancelled.action_confirm()
    assert offers[0].stock_quantity==1
    cancelled.action_cancel()
    assert offers[0].stock_quantity==2 and cancelled.wah_route_state=='cancelled' and cancelled.wah_collection_state=='not_required'
    print('PASS: cancelar antes del retiro repone stock y no deja una deuda de cobro')
finally:
    env.cr.rollback()
    print('Pruebas revertidas. Sin correos, cobros reales ni datos ficticios persistidos.')
