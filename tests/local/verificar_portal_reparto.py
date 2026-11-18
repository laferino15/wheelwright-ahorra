"""Comercio y repartidor con permisos reales; todo se revierte al finalizar."""
from datetime import timedelta
import secrets
from types import SimpleNamespace
from werkzeug.wrappers import Request as HttpRequest
from odoo.http import _request_stack
from odoo.exceptions import AccessError, ValidationError
assert env.cr.dbname == 'wheelwright_ahorra_dev'

def denied(call, exception=ValidationError):
    try:
        with env.cr.savepoint(): call()
    except exception: return
    raise AssertionError('La operación debía rechazarse')

class Session(dict):
    debug = ''

def render_fragment(template, values, user, website):
    request_env=env(user=user.id)
    mock=SimpleNamespace(env=request_env,website=website,session=Session(),cookies={},
        is_frontend=True,website_routing=website.id,httprequest=HttpRequest.from_values(path='/mi-reparto',base_url='http://127.0.0.1:8070'),
        csrf_token=lambda:'CSRF-FICTICIO')
    _request_stack.push(mock)
    try:
        arch=request_env.ref('wheelwright_ahorra.'+template).sudo()._get_combined_arch()
        for node in arch.xpath('.//t[@t-call="portal.portal_layout" or @t-call="wheelwright_ahorra.courier_layout" or @t-call="wheelwright_ahorra.merchant_layout"]'):
            del node.attrib['t-call']
        return str(request_env['ir.qweb']._render(arch,dict(values,website=website)))
    finally:
        _request_stack.pop()

try:
    token=secrets.token_hex(5)
    site=env['website'].browse(1)
    manager=env['res.users'].sudo().with_context(no_reset_password=True).create({'name':'ADMIN FICTICIO PORTAL','login':'admin-portal-'+token+'@example.invalid','group_ids':[(6,0,[env.ref('base.group_user').id,env.ref('product.group_product_manager').id,env.ref('sales_team.group_sale_manager').id])]})
    users=env['res.users'].sudo().with_context(no_reset_password=True).create([{'name':'USUARIO FICTICIO PORTAL '+str(i),'login':token+str(i)+'@example.invalid','group_ids':[(6,0,env.ref('base.group_portal').ids)]} for i in range(5)])
    users[4].partner_id.write({'street':'DESTINO FICTICIO','phone':'000000'})
    stores=env['wah.merchant'].sudo().create([{'name':'LOCAL FICTICIO PORTAL '+str(i)+token,'owner_id':users[i].id,'website_id':site.id,'category_id':9,'street':'ORIGEN FICTICIO','phone':'000000'} for i in range(2)])
    stores.action_approve()
    products=env['product.template'].sudo().create([{'name':'PRODUCTO FICTICIO PORTAL '+str(i),'type':'consu','sale_ok':True,'list_price':100,'wah_store_id':store.partner_id.id,'website_id':site.id,'is_published':True,'taxes_id':[(5,0,0)]} for i,store in enumerate(stores)])
    def make_order():
        order=env['sale.order'].sudo().with_context(send_email=False,tracking_disable=True,mail_notrack=True).create({'partner_id':users[4].partner_id.id,'website_id':site.id,'wah_delivery_date':env['sale.order']._wah_local_now().date()+timedelta(days=1),'wah_delivery_window':'midday','order_line':[(0,0,{'product_id':product.product_variant_id.id,'product_uom_qty':1,'price_unit':100,'tax_ids':[(5,0,0)]}) for product in products]+[(0,0,{'product_id':1,'product_uom_qty':1,'price_unit':25,'is_delivery':True,'tax_ids':[(5,0,0)]})]})
        order.action_confirm()
        return order
    order=make_order()
    other=make_order()
    a=order.wah_preparation_ids.filtered(lambda p:p.merchant_id==stores[0]).with_user(users[0])
    b=order.wah_preparation_ids.filtered(lambda p:p.merchant_id==stores[1]).with_user(users[1])
    denied(a.action_request_pickup)
    denied(lambda:b.with_user(users[0]).action_request_pickup(),AccessError)
    a.action_start();a.action_ready();a.action_request_pickup()
    event_count=len(order.wah_route_event_ids)
    a.action_request_pickup();assert len(order.wah_route_event_ids)==event_count
    b.action_start();b.action_ready();b.action_request_pickup()
    assert a.pickup_requested_by==users[0] and b.pickup_requested_by==users[1]
    denied(a.action_merchant_handoff)
    couriers=env['wah.courier'].with_user(manager).create([{'name':'REPARTIDOR FICTICIO '+str(i),'phone':'000000','user_id':users[i+2].id} for i in range(2)])
    admin=order.with_user(manager)
    admin.write({'wah_courier_id':couriers[0].id});admin.action_wah_assign()
    courier=order.with_user(users[2])
    denied(lambda:order.with_user(users[3])._wah_courier_summary(site),AccessError)
    denied(lambda:order.with_user(users[4])._wah_courier_summary(site),AccessError)
    denied(courier.action_wah_dispatch,AccessError)
    denied(lambda: courier._wah_courier_action(site,'depart'))
    summary=courier._wah_courier_summary(site,detail=True)
    assert len(summary['pickups'])==2 and summary['amount']==225 and not summary['accepted']
    assert summary['customer']==users[4].partner_id.name
    html=render_fragment('courier_route_detail',{'route':summary,'error':False,'updated':False},users[2],site)
    assert 'Aceptar recorrido' in html and 'DESTINO FICTICIO' in html
    merchant_html=render_fragment('merchant_preparation_detail',{'preparation':a,'updated':False,'error':False,'pickup_info':{'courier':couriers[0].name,'phone':'000','assigned':True}},users[0],site)
    assert 'Confirmar entrega al repartidor' in merchant_html
    courier._wah_courier_action(site,'accept')
    assert order.wah_courier_accepted_at
    a.action_merchant_handoff()
    assert a.state=='collected' and b.state=='ready'
    a.action_merchant_handoff()
    denied(lambda:courier._wah_courier_action(site,'depart'))
    denied(lambda:courier._wah_courier_action(site,'pickup',preparation_id=other.wah_preparation_ids[:1].id),AccessError)
    courier._wah_courier_action(site,'pickup',preparation_id=b.id)
    assert b.state=='collected'
    courier._wah_courier_action(site,'depart')
    assert order.wah_route_state=='on_way'
    denied(lambda:courier._wah_courier_action(site,'collect',method='cash',received=225))
    courier._wah_courier_action(site,'deliver')
    assert order.wah_route_state=='delivered' and all(p.state=='delivered' for p in order.wah_preparation_ids)
    assert order.wah_collection_state=='pending'
    html=render_fragment('courier_route_detail',{'route':courier._wah_courier_summary(site,detail=True),'error':False,'updated':False},users[2],site)
    assert 'Confirmar cobro recibido' in html
    denied(lambda:courier._wah_courier_action(site,'collect',method='cash',received=224))
    receipt=courier._wah_courier_action(site,'collect',method='cash',received=275)
    assert receipt.amount==225 and receipt.change_amount==50 and receipt.actor_id==users[2]
    assert order.wah_collection_state=='collected'
    denied(lambda:courier._wah_courier_action(site,'collect',method='cash',received=225))
    assert any(event.actor_id==users[0] for event in order.wah_route_event_ids)
    assert any(event.actor_id==users[2] for event in order.wah_route_event_ids)
    print('PASS: dos locales, solicitud, entrega por comercio, retiro por repartidor, entrega completa y cobro único con vuelto y responsable')
    other_admin=other.with_user(manager)
    other_admin.write({'wah_courier_id':couriers[0].id});other_admin.action_wah_assign()
    other.with_user(users[2])._wah_courier_action(site,'accept')
    other_admin.write({'wah_courier_id':couriers[1].id})
    assert not other.wah_courier_accepted_at
    denied(lambda:other.with_user(users[2])._wah_courier_summary(site),AccessError)
    other.with_user(users[3])._wah_courier_action(site,'accept')
    couriers[1].write({'active':False})
    denied(lambda:other.with_user(users[3])._wah_courier_summary(site),AccessError)
    couriers[1].write({'active':True})
    assert other.with_user(users[3])._wah_courier_summary(site)['accepted']
    users[3].sudo().write({'active':False})
    denied(lambda:other.with_user(users[3])._wah_courier_summary(site),AccessError)
    users[3].sudo().write({'active':True})
    denied(lambda:env['wah.courier'].with_user(users[2]).search([]),AccessError)
    denied(lambda:other.with_user(users[4]).read(['wah_courier_id']),AccessError)
    print('PASS: acceso exclusivo al recorrido propio, cambio de repartidor revoca acceso y reinicia aceptación; cuentas inactivas bloqueadas')
    print('RESULTADO: PORTALES DE RETIRO Y REPARTO APROBADOS')
finally:
    env.cr.rollback()
    print('Rollback completo. Sin entregas, cobros ni datos ficticios persistidos.')
