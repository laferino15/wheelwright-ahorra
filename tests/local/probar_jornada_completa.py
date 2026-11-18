"""Jornada funcional local: HTTP/RPC, COD nativo y concurrencia. Fixtures propios."""
import hashlib
import json
import secrets
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

import requests
from lxml import html
from psycopg2.errors import DeadlockDetected, SerializationFailure
from odoo import api
from odoo.exceptions import ValidationError

assert env.cr.dbname == 'wheelwright_ahorra_dev'
ROOT = Path(__file__).resolve().parent
BASE = 'http://127.0.0.1:8070'
TOKEN = secrets.token_hex(5)
started = time.monotonic()
users = env['res.users']; partners = env['res.partner']; stores = env['wah.merchant']
offers = env['wah.merchant.product']; products = env['product.template']; couriers = env['wah.courier']
sessions = []; checks = []; cases = []; failure = None; cleanup_error = None
suppressed_mails = 0

def refresh():
    env.cr.rollback(); env.invalidate_all()

def mark(name, details=''):
    checks.append({'test': name, 'result': 'PASS', 'details': details})
    print('PASS:', name, flush=True)

def get(session, path):
    response = session.get(BASE + path, timeout=35)
    assert response.status_code == 200, (path, response.status_code)
    return response, html.fromstring(response.content)

def csrf(tree):
    return tree.xpath('//input[@name="csrf_token"]/@value')[0]

def jsonrpc(session, path, params, error=False):
    response = session.post(BASE + path, json={'jsonrpc':'2.0','method':'call','params':params,'id':1}, timeout=40)
    assert response.status_code == 200, (path, response.status_code)
    body = response.json()
    if error:
        assert 'error' in body, path
    else:
        assert 'error' not in body, (path, body.get('error',{}).get('data',{}).get('message'))
    return body if error else body.get('result')

def rpc(session, model, method, args=None, kwargs=None, error=False):
    return jsonrpc(session, f'/web/dataset/call_kw/{model}/{method}',
        {'model':model,'method':method,'args':args or [],'kwargs':kwargs or {}}, error)

def baseline():
    return {
        'products': {p.id:[p.name,p.list_price,p.website_published,hashlib.sha256(p.image_1920 or b'').hexdigest()] for p in env['product.template'].sudo().with_context(active_test=False).search([])},
        'offers': {p.id:[p.state,p.stock_tracking,p.stock_quantity,p.available,p.product_tmpl_id.id] for p in env['wah.merchant.product'].sudo().search([])},
        'orders': {o.id:[o.state,o.amount_total,o.wah_route_state,o.wah_collection_state,str(o.wah_delivery_date),o.wah_delivery_window] for o in env['sale.order'].sudo().search([])},
    }

before = baseline()
snapshot_hash = hashlib.sha256(json.dumps(before, sort_keys=True).encode()).hexdigest()

def address(session, number, depth=0):
    assert depth < 4, 'El checkout repite la solicitud de dirección'
    response, tree = get(session, '/shop/checkout?try_skip_step=true')
    if '/shop/address' not in response.url:
        return
    form = tree.xpath('//form[@name="address_form"]')[0]
    data = {item.get('name'): item.get('value','') for item in form.xpath('.//input[@name]') if item.get('type') != 'checkbox'}
    for select in form.xpath('.//select[@name]'):
        chosen = select.xpath('./option[@selected]/@value') or select.xpath('./option[1]/@value')
        if chosen: data[select.get('name')] = chosen[0]
    data.update(name=f'COMPRADOR FICTICIO JORNADA {number}', phone='0000000000',
        street=f'DOMICILIO FICTICIO {number} - NO ENTREGAR', street2='PRUEBA INTERNA',
        email=users[number+4].login, wah_delivery_notes='SIMULACION - NO PREPARAR PEDIDOS REALES')
    response = session.post(BASE+'/shop/address/submit', data=data, timeout=35)
    assert response.status_code == 200
    feedback = response.json()
    assert feedback.get('redirectUrl'), feedback
    next_response, _ = get(session, feedback['redirectUrl'])
    if '/shop/address' in next_response.url:
        address(session, number, depth+1)

def cart(session, buyer_number, items, slot):
    for index, qty in items:
        product = offers[index].sudo().product_tmpl_id
        jsonrpc(session, '/shop/cart/add', {'product_template_id':product.id,'product_id':product.product_variant_id.id,'quantity':qty})
    address(session, buyer_number)
    response, tree = get(session, '/shop/payment')
    assert '/shop/entrega' in response.url, response.url
    token = csrf(tree)
    result = session.post(BASE+'/shop/entrega', data={'csrf_token':token,'delivery_date':day,'delivery_window':slot}, timeout=35)
    assert result.status_code == 200 and '/shop/payment' in result.url, (result.status_code,result.url)
    assert 'Efectivo al recibir' in result.text and 'Entrega elegida' in result.text
    refresh()
    order = env['sale.order'].sudo().search([('partner_id','=',users[buyer_number+4].partner_id.id),('website_id','=',1),('state','=','draft')], order='id desc', limit=1)
    assert order and order.wah_delivery_window == slot and str(order.wah_delivery_date) == day
    assert len(order.order_line.filtered(lambda line:not line.is_delivery and not line.display_type)) == len(items)
    return order

def cod_confirm(session, order):
    global suppressed_mails
    token = order._portal_ensure_token(); env.cr.commit()
    jsonrpc(session, f'/shop/payment/transaction/{order.id}', {
        'access_token':token,'provider_id':provider.id,'payment_method_id':method.id,
        'token_id':None,'amount':order.amount_total,'flow':'redirect','tokenization_requested':False,
        'landing_route':'/shop/payment/validate'})
    refresh(); transaction = order.transaction_ids.sorted('id')[-1]
    response = session.post(BASE+'/payment/custom/process', data={'reference':transaction.reference}, allow_redirects=False, timeout=30)
    assert response.status_code == 303 or response.status_code == 302
    refresh(); assert transaction.state == 'pending'
    # Ejecuta la confirmación COD nativa, pero silencia únicamente los correos
    # de este proceso de pruebas. El servidor y los usuarios reales no se alteran.
    with patch.object(type(env['sale.order']), '_send_order_notification_mail', return_value=None) as mail:
        transaction.with_context(tracking_disable=True,mail_notrack=True)._post_process()
        suppressed_mails += mail.call_count
    env.cr.commit(); refresh()
    assert order.state == 'sale' and transaction.state == 'pending' and transaction.is_post_processed
    assert not transaction.payment_id and not order.invoice_ids
    response, _ = get(session, '/shop/payment/validate')
    assert '/shop/confirmation' in response.url and 'Entrega programada' in response.text
    return transaction

def fulfill(order, courier, cash=True, collect=True):
    rpc(admin, 'sale.order', 'write', [[order.id], {'wah_courier_id':courier.id}])
    rpc(admin, 'sale.order', 'action_wah_assign', [[order.id]])
    rpc(admin, 'sale.order', 'action_wah_dispatch', [[order.id]], error=True)
    refresh()
    preps = order.wah_preparation_ids
    for prep in preps:
        owner_session = sessions[1 + stores.ids.index(prep.merchant_id.id)]
        response, tree = get(owner_session, f'/mi-comercio/pedidos/{prep.id}')
        assert order.wah_delivery_label in html.fromstring(response.content).text_content()
        form_token = csrf(tree)
        for action in ['start','ready']:
            response = owner_session.post(BASE+f'/mi-comercio/pedidos/{prep.id}/actualizar', data={'csrf_token':form_token,'action':action}, timeout=30)
            assert response.status_code == 200
        rpc(admin, 'wah.preparation', 'action_collect', [[prep.id]])
    rpc(admin, 'sale.order', 'action_wah_dispatch', [[order.id]])
    refresh(); assert order.wah_preparation_state == 'on_way'
    buyer_session = buyer_by_partner[order.partner_id.id]
    response, _ = get(buyer_session, f'/my/orders/{order.id}')
    assert 'En camino' in response.text and 'Pendiente de cobro' in response.text
    rpc(admin, 'sale.order', 'action_wah_deliver', [[order.id]])
    refresh(); assert order.wah_collection_state == 'pending'
    if not collect: return False
    total = order.amount_total
    result = rpc(admin, 'wah.collection.register', 'create', [{
        'order_id':order.id,'amount':total,'method':'cash' if cash else 'transfer',
        'received_amount':total+100 if cash else 0,'reference':'' if cash else 'TRANSFERENCIA-FICTICIA-'+TOKEN}])
    wizard = result[0] if isinstance(result,list) else result
    receipt_action = rpc(admin,'wah.collection.register','action_register',[[wizard]])
    rpc(admin,'wah.collection.register','action_register',[[wizard]],error=True)
    refresh(); receipt=env['wah.collection'].sudo().browse(receipt_action['res_id'])
    assert receipt.amount == order.amount_total and order.wah_collection_state == 'collected'
    assert receipt.change_amount == (100 if cash else 0)
    response, _ = get(buyer_session, f'/my/orders/{order.id}')
    assert 'Entregado' in response.text and 'Cobro registrado' in response.text
    return receipt

try:
    provider = env['payment.provider'].sudo().browse(25)
    assert provider.code == 'custom' and provider.custom_mode == 'cash_on_delivery' and provider.state == 'enabled'
    method = provider.payment_method_ids[:1]
    assert method
    day = (env['sale.order']._wah_local_now().date()+timedelta(days=1)).isoformat()
    for i in range(8):
        password=secrets.token_urlsafe(28)
        groups=[env.ref('base.group_user').id,env.ref('product.group_product_manager').id,env.ref('sales_team.group_sale_manager').id] if i==0 else env.ref('base.group_portal').ids
        user=env['res.users'].sudo().with_context(no_reset_password=True,tracking_disable=True).create({
            'name':f'PRUEBA JORNADA {i}','login':f'jornada-{TOKEN}-{i}@example.invalid','password':password,'group_ids':[(6,0,groups)]})
        users |= user; partners |= user.partner_id; env.cr.commit()
        session=requests.Session();session.trust_env=False
        auth=jsonrpc(session,'/web/session/authenticate',{'db':env.cr.dbname,'login':user.login,'password':password})
        assert auth.get('uid')==user.id
        sessions.append(session)
    admin=sessions[0]
    for i, category in enumerate([9,10,15]):
        seller=sessions[i+1]
        _,tree=get(seller,'/mi-comercio/registro')
        response=seller.post(BASE+'/mi-comercio/registro',data={'csrf_token':csrf(tree),'name':f'LOCAL PRUEBA JORNADA {TOKEN} {i}',
            'street':'LOCAL FICTICIO - NO RETIRAR','phone':'0000000','category_id':str(category)},timeout=30)
        assert response.status_code==200
        refresh()
        store=env['wah.merchant'].sudo().search([('owner_id','=',users[i+1].id)],limit=1)
        assert store and store.state=='pending'
        stores|=store
        rpc(admin,'wah.merchant','action_approve',[[store.id]])
        refresh(); partners|=store.partner_id
        for j in range(2):
            _,tree=get(seller,'/mi-comercio/productos/nuevo')
            photo=ROOT/'fixtures'/(['milanesas.png','pan.png','tarta.png'][i])
            response=seller.post(BASE+'/mi-comercio/productos/nuevo', data={'csrf_token':csrf(tree),
                'name':f'PRUEBA JORNADA {TOKEN} {i}-{j}','presentation':'unidad','description':'SIMULACION - NO COMPRAR',
                'category_id':str(category),'price':'100','available':'1','stock_tracking':'1','stock_quantity':'2' if i==2 and j==1 else '6','intent':'submit'},
                files={'image':(photo.name,photo.read_bytes(),'image/png')}, timeout=35)
            assert response.status_code==200 and 'enviado a revisión' in response.text
            refresh()
            offer=env['wah.merchant.product'].sudo().search([('merchant_id','=',store.id),('name','=',f'PRUEBA JORNADA {TOKEN} {i}-{j}')],limit=1)
            assert offer.state=='pending'
            offers|=offer
            rpc(admin,'wah.merchant.product','action_approve',[[offer.id]])
            refresh();products|=offer.product_tmpl_id
    mark('Registro y aprobación de 3 locales; 6 productos con imagen, precio y stock publicados')
    couriers=env['wah.courier'].sudo().create([{'name':f'REPARTIDOR FICTICIO JORNADA {TOKEN} {i}','phone':'0000000'} for i in range(2)])
    env.cr.commit()
    buyer_by_partner={users[i+4].partner_id.id:sessions[i+4] for i in range(4)}
    definitions=[('Mediodía',0,[(0,2),(2,1)],'midday'),('Tarde',1,[(3,1),(4,2)],'afternoon'),
                 ('Noche',2,[(1,1),(5,1)],'night'),('Cancelación',3,[(0,1)],'midday')]
    main=[]
    for name,buyer_number,items,slot in definitions:
        order=cart(sessions[buyer_number+4],buyer_number,items,slot)
        cod_confirm(sessions[buyer_number+4],order)
        expected_stores={offers[index].merchant_id.id for index,_qty in items}
        assert set(order.wah_preparation_ids.merchant_id.ids)==expected_stores
        main.append(order)
        cases.append({'scenario':name,'order':order.name,'slot':slot,'products':len(items),'stores':len(expected_stores)})
    mark('Compra nativa: carrito, dirección, franjas y confirmación Efectivo al recibir en 4 pedidos')
    cancelled=main[3]
    rpc(admin,'sale.order','action_cancel',[[cancelled.id]],{'context':{'disable_cancel_warning':True,'tracking_disable':True}})
    refresh(); assert cancelled.state=='cancel' and cancelled.wah_route_state=='cancelled' and cancelled.wah_collection_state=='not_required'
    assert offers[0].stock_quantity==4
    mark('Cancelación antes del retiro: devuelve stock y no deja cobro pendiente')
    receipts=[]
    for i,order in enumerate(main[:3]):
        receipts.append(fulfill(order,couriers[i%2],cash=i!=1))
    mark('Preparación por cada dueño, retiros, reparto y entrega de pedidos con varios locales')
    mark('Cobros en efectivo con vuelto y transferencia verificada; segundo cobro bloqueado')
    last=main[2];old=receipts[2]
    v=rpc(admin,'wah.collection.void','create',[{'collection_id':old.id,'reason':'Corrección ficticia del registro durante la jornada de pruebas'}])
    rpc(admin,'wah.collection.void','action_void',[[v[0] if isinstance(v,list) else v]])
    refresh();assert old.state=='void' and last.wah_collection_state=='pending'
    w=rpc(admin,'wah.collection.register','create',[{'order_id':last.id,'amount':last.amount_total,'method':'cash','received_amount':last.amount_total}])
    rpc(admin,'wah.collection.register','action_register',[[w[0] if isinstance(w,list) else w]])
    refresh();assert last.wah_collection_state=='collected' and len(last.wah_collection_ids)==2
    mark('Corrección de cobro: original anulado con motivo y nuevo registro, sin borrar historial')
    for owner_number,order in [(2,main[0]),(0,main[1])]:
        prep=order.wah_preparation_ids[0]
        response=sessions[owner_number+1].get(BASE+f'/mi-comercio/pedidos/{prep.id}',timeout=25)
        assert response.status_code==404
    rpc(sessions[4],'sale.order','action_wah_dispatch',[[main[0].id]],error=True)
    rpc(sessions[4],'wah.collection','read',[[receipts[0].id],['amount']],error=True)
    mark('Aislamiento entre locales y bloqueo de reparto/cobros para clientes')
    race=[]
    for buyer_number in [0,1]:
        race.append(cart(sessions[buyer_number+4],buyer_number,[(5,1)],'night'))
    registry=env.registry;manager_id=users[0].id
    def confirm(order_id):
        for attempt in range(5):
            with registry.cursor() as cr:
                thread_env=api.Environment(cr,manager_id,{'send_email':False,'tracking_disable':True,'mail_notrack':True})
                try:
                    thread_env['sale.order'].browse(order_id).action_confirm();cr.commit();return 'confirmed'
                except ValidationError:
                    cr.rollback();return 'blocked'
                except (SerializationFailure,DeadlockDetected):cr.rollback()
        raise AssertionError('No se resolvió el conflicto de stock')
    env.cr.commit()
    with ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(confirm,[o.id for o in race]))
    refresh();assert sorted(results)==['blocked','confirmed'] and offers[5].stock_quantity==0,results
    winner=next(o for o in race if o.state=='sale')
    loser=next(o for o in race if o.state=='draft')
    fulfill(winner,couriers[1],collect=False)
    refresh();assert winner.wah_route_state=='delivered' and winner.wah_collection_state=='pending'
    expected=[4,5,5,5,4,0]
    assert [offer.stock_quantity for offer in offers]==expected
    _,tree=get(sessions[4],offers[5].product_tmpl_id.website_url)
    assert tree.xpath('//a[@id="add_to_cart" and contains(@class,"disabled")]')
    mark('Última unidad: una sola compra confirmada; stock final exacto y producto agotado')
    cases.extend([{'scenario':'Última unidad ganadora','order':winner.name,'slot':'night','result':'Entregado pendiente de cobro'},
                  {'scenario':'Última unidad perdedora','order':loser.name,'slot':'night','result':'Confirmación bloqueada por stock'}])
    pending=env['sale.order'].sudo().search([('id','in',[o.id for o in main+race]),('state','=','sale'),('wah_route_state','=','delivered'),('wah_collection_state','=','pending')])
    assert pending.ids==winner.ids
    all_orders=env['sale.order'].sudo().search([('partner_id','in',users[4:].partner_id.ids)])
    assert len(all_orders)==6
    active=all_orders.wah_collection_ids.filtered(lambda record:record.state=='posted')
    assert len(active)==3 and sum(active.mapped('amount'))==sum(o.amount_total for o in main[:3])
    assert not all_orders.invoice_ids and not all_orders.transaction_ids.payment_id
    assert not env['mail.mail'].sudo().search_count([('model','=','sale.order'),('res_id','in',all_orders.ids)])
    mark('Conciliación de la jornada: 4 entregados, 3 cobrados, 1 sin cobrar, 1 cancelado y 1 bloqueado')
    mark('Sin facturas, pagos contables ni correos generados por los pedidos de prueba',f'{suppressed_mails} envíos de notificación suprimidos en el proceso de prueba')
except Exception:
    failure=traceback.format_exc()
    print('FALLO:',failure,flush=True)
finally:
    try:
        refresh()
        fixture_orders=env['sale.order'].sudo().search([('partner_id','in',users.partner_id.ids)]) if users else env['sale.order']
        children=env['res.partner'].sudo().search([('parent_id','in',partners.ids)]) if partners else env['res.partner']
        partners|=children
        if fixture_orders:
            fixture_orders.wah_collection_ids.sudo().unlink()
            fixture_orders.sudo().with_context(tracking_disable=True).write({'wah_route_state':'pending'})
            fixture_orders.wah_preparation_ids.sudo().write({'state':'ready'})
            transactions=fixture_orders.transaction_ids
            pickings=fixture_orders.picking_ids
            fixture_orders.with_context(disable_cancel_warning=True,tracking_disable=True).action_unlock()
            fixture_orders.with_context(disable_cancel_warning=True,tracking_disable=True).action_cancel()
            fixture_orders.wah_preparation_ids.sudo().unlink();pickings.sudo().unlink()
            transactions.sudo().unlink();fixture_orders.wah_route_event_ids.sudo().unlink();fixture_orders.sudo().unlink()
        values=env['product.value'].sudo().search([('user_id','in',users.ids)]) if users else env['product.value']
        assert all(not value.product_id or value.product_id.product_tmpl_id in products for value in values)
        values.unlink()
        offers.sudo().exists().unlink();products.sudo().exists().unlink();stores.sudo().exists().unlink();couriers.sudo().exists().unlink()
        users.sudo().exists().unlink();partners.sudo().exists().unlink();env.cr.commit();refresh()
        assert baseline()==before,'Cambió algún dato de negocio preexistente; revisar el alcance antes de concluir.'
        assert not env['res.users'].sudo().with_context(active_test=False).search_count([('login','=like',f'jornada-{TOKEN}-%')])
        mark('Limpieza completa y datos de negocio preexistentes conservados')
    except Exception:
        cleanup_error=traceback.format_exc()
        print('ERROR DE LIMPIEZA:',cleanup_error,flush=True)
    report={'run':TOKEN,'duration_seconds':round(time.monotonic()-started,2),'delivery_day':locals().get('day'),
        'checks':checks,'scenarios':cases,'failure':failure,'cleanup_error':cleanup_error,'original_data_hash':snapshot_hash,
        'scope':'HTTP y RPC locales, postproceso COD nativo con notificaciones suprimidas y prueba de confirmaciones concurrentes. Sin dinero, correos o entregas reales.'}
    (ROOT/'resultado_jornada_completa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# Resultado de la jornada de pruebas','',f"Resultado: {'APROBADA' if not failure and not cleanup_error else 'REQUIERE REVISIÓN'}",'',report['scope'],'',f"Duración: {report['duration_seconds']} segundos.",'','| Comprobación | Resultado |','|---|---|']
    lines += [f"| {check['test']} | {check['result']} |" for check in checks]
    lines += ['','| Escenario | Pedido ficticio | Franja |','|---|---|---|']+[f"| {case['scenario']} | {case['order']} | {case['slot']} |" for case in cases]
    if failure:lines+=['','## Error detectado','', '```',failure,'```']
    if cleanup_error:lines+=['','## Limpieza pendiente','', '```',cleanup_error,'```']
    (ROOT/'RESULTADO_JORNADA.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
if failure or cleanup_error:raise AssertionError('La jornada requiere revisión. Ver resultado_jornada_completa.json.')
