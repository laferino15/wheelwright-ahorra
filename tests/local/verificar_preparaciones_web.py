"""Prueba web aislada con dos vendedores y comprador ficticios. Limpia los datos."""
import secrets
import requests
from lxml import html

assert env.cr.dbname == 'wheelwright_ahorra_dev'
base = 'http://127.0.0.1:8070'
users = env['res.users']; stores = env['wah.merchant']; products = env['product.template']
partners = env['res.partner']; orders = env['sale.order']; sessions = []
token = secrets.token_hex(5)

def refresh():
    env.cr.rollback(); env.invalidate_all()

def get(session, path, status=200):
    response = session.get(base+path, timeout=25)
    assert response.status_code == status, (path, response.status_code)
    return response, html.fromstring(response.content)

def csrf(tree):
    return tree.xpath('//input[@name="csrf_token"]/@value')[0]

try:
    for i in range(3):
        password = secrets.token_urlsafe(24)
        login = f'preparacion-web-{token}-{i}@example.invalid'
        user = env['res.users'].sudo().with_context(no_reset_password=True, tracking_disable=True).create({
            'name':f'PRUEBA FLUJO {token} {i}', 'login':login, 'password':password,
            'group_ids':[(6,0,env.ref('base.group_portal').ids)],
        })
        users |= user; partners |= user.partner_id; env.cr.commit()
        session=requests.Session(); session.trust_env=False
        auth=session.post(base+'/web/session/authenticate', json={'jsonrpc':'2.0','method':'call',
            'params':{'db':env.cr.dbname,'login':login,'password':password},'id':1},timeout=25).json()
        assert auth.get('result',{}).get('uid') == user.id
        sessions.append(session)
    stores=env['wah.merchant'].sudo().create([
        {'name':f'LOCAL WEB PREPARACION {token} {i}', 'owner_id':users[i].id, 'website_id':1,
         'category_id':9, 'street':'LOCAL FICTICIO', 'phone':'0000000000'} for i in range(2)
    ])
    stores.action_approve(); partners |= stores.mapped('partner_id')
    products=env['product.template'].sudo().create([
        {'name':f'PRODUCTO PRIVADO LOCAL {i} {token}', 'type':'consu', 'list_price':100,
         'wah_store_id':stores[i].partner_id.id, 'website_id':1} for i in range(2)
    ])
    users[2].partner_id.write({'street':'DOMICILIO_CLIENTE_NO_COMPARTIR', 'phone':'9999999999'})
    orders=env['sale.order'].sudo().with_context(tracking_disable=True).create({
        'partner_id':users[2].partner_id.id,'website_id':1,
        'order_line':[(0,0,{'product_id':product.product_variant_id.id,'product_uom_qty':i+1}) for i,product in enumerate(products)],
    })
    orders.with_context(send_email=False,tracking_disable=True).action_confirm()
    tickets=orders.wah_preparation_ids
    own=tickets.filtered(lambda item:item.merchant_id==stores[0])
    other=tickets-own
    env.cr.commit()
    session=sessions[0]
    response,tree=get(session,'/mi-comercio')
    assert 'Ver pedidos de mi local' in response.text
    response,tree=get(session,'/mi-comercio/pedidos')
    assert orders.name in response.text
    response,tree=get(session,f'/mi-comercio/pedidos/{own.id}')
    assert products[0].name in response.text and products[1].name not in response.text
    assert 'DOMICILIO_CLIENTE_NO_COMPARTIR' not in response.text and users[2].name not in response.text
    get(session,f'/mi-comercio/pedidos/{other.id}',404)
    get(sessions[2],f'/mi-comercio/pedidos/{own.id}',404)
    print('PASS: acceso desde Mi comercio y aislamiento de productos y datos del comprador')

    url=base+f'/mi-comercio/pedidos/{own.id}/actualizar'
    assert session.post(url,data={'action':'start'},timeout=25).status_code==400
    response=session.post(url,data={'csrf_token':csrf(tree),'action':'ready'},timeout=25)
    assert response.status_code==200
    refresh(); assert own.state=='received'
    response=session.post(url,data={'csrf_token':csrf(tree),'action':'deliver'},timeout=25)
    assert response.status_code==200
    refresh(); assert own.state=='received'
    for action,state in [('start','preparing'),('ready','ready')]:
        response=session.post(url,data={'csrf_token':csrf(tree),'action':action},timeout=25)
        assert response.status_code==200
        refresh(); assert own.state==state
    print('PASS: botones recibido -> preparación -> listo, CSRF y bloqueo de acciones administrativas')

    response=session.post(url,data={'csrf_token':csrf(tree),'action':'note','merchant_note':'Observación ficticia para el retiro'},timeout=25)
    refresh(); assert own.merchant_note=='Observación ficticia para el retiro'
    other.action_start(); other.action_ready(); tickets.action_collect(); tickets.action_deliver(); env.cr.commit()
    response,tree=get(sessions[2],f'/my/orders/{orders.id}')
    assert 'Estado de tu pedido:' in response.text and 'Entregado' in tree.text_content()
    refresh(); assert not orders.transaction_ids
    print('PASS: observación al coordinador, retiro/entrega administrativos y estado visible al comprador sin pagos')
finally:
    refresh()
    if orders.exists():
        pickings=orders.picking_ids
        orders.action_unlock()
        orders.action_cancel()
        orders.wah_preparation_ids.sudo().unlink()
        pickings.sudo().unlink()
        orders.sudo().unlink()
    products.sudo().exists().unlink()
    stores.sudo().exists().unlink()
    users.sudo().exists().unlink()
    partners.sudo().exists().unlink()
    env.cr.commit()
    print('Datos ficticios eliminados. No se enviaron correos ni se registraron cobros.')
