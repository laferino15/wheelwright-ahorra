"""Recorrido HTTP con dos cuentas ficticias que se eliminan al terminar."""
import base64
import secrets
import requests
from lxml import html

assert env.cr.dbname == 'wheelwright_ahorra_dev'
base = 'http://127.0.0.1:8070'
token = secrets.token_hex(5)
users = env['res.users']
stores = env['wah.merchant']
actuals = env['product.template']
partners = env['res.partner']
sessions = []

def get(session, path):
    response = session.get(base + path, timeout=25)
    assert response.status_code == 200, (path, response.status_code)
    return response, html.fromstring(response.content)

def csrf(tree):
    return tree.xpath('//input[@name="csrf_token"]/@value')[0]

try:
    for n in [1, 2]:
        password = secrets.token_urlsafe(24)
        login = f'prueba-web-{token}-{n}@example.invalid'
        user = env['res.users'].sudo().with_context(no_reset_password=True, tracking_disable=True).create({
            'name': f'PRUEBA WEB COMERCIO {token} {n}', 'login': login, 'password': password,
            'group_ids': [(6, 0, env.ref('base.group_portal').ids)],
        })
        users |= user
        partners |= user.partner_id
        env.cr.commit()
        session = requests.Session(); session.trust_env = False
        result = session.post(base+'/web/session/authenticate', json={
            'jsonrpc':'2.0','method':'call','params':{'db':env.cr.dbname,'login':login,'password':password},'id':1,
        },timeout=25).json()
        assert result.get('result',{}).get('uid') == user.id, 'No se pudo iniciar la sesión de prueba'
        sessions.append(session)

    session=sessions[0]
    response, tree = get(session, '/mi-comercio/registro')
    response=session.post(base+'/mi-comercio/registro',data={
        'csrf_token':csrf(tree),'name':f'LOCAL WEB PRUEBA {token}','category_id':'9',
        'street':'DOMICILIO FICTICIO - NO OPERAR','phone':'0000000000','hours':'Prueba técnica',
        'owner_id':str(users[1].id), 'state':'approved',
    },timeout=25)
    assert response.status_code==200 and 'Tu local' in response.text
    env.cr.rollback(); env.invalidate_all()
    store=env['wah.merchant'].sudo().search([('owner_id','=',users[0].id)])
    stores |= store
    assert store.owner_id.id==users[0].id and store.state=='pending'
    print('PASS: registro web fuerza dueño y deja el local pendiente de aprobación')
    store.action_approve(); partners |= store.partner_id; env.cr.commit()

    response, tree=get(session,'/mi-comercio/productos/nuevo')
    image=base64.b64decode(env['product.template'].browse(59).image_128)
    response=session.post(base+'/mi-comercio/productos/nuevo',data={
        'csrf_token':csrf(tree),'name':'PRODUCTO WEB DE PRUEBA','category_id':'9',
        'presentation':'unidad','description':'Prueba del panel de comercio','price':'121','available':'1',
    },files={'image':('producto.png',image,'image/png')},timeout=25)
    assert response.status_code==200 and 'PRODUCTO WEB DE PRUEBA' in response.text
    env.cr.rollback(); env.invalidate_all()
    product=env['wah.merchant.product'].sudo().search([('merchant_id','=',store.id)])
    assert product.state=='draft' and product.image
    response, tree=get(session,f'/mi-comercio/productos/{product.id}')
    assert 'Imagen actual del producto' in response.text
    denied=sessions[1].get(base+f'/mi-comercio/productos/{product.id}',timeout=25)
    assert denied.status_code==404,denied.status_code
    print('PASS: carga de imagen, borrador, edición y bloqueo HTTP de otro comerciante')
    no_csrf=session.post(base+f'/mi-comercio/productos/{product.id}/enviar',timeout=25)
    assert no_csrf.status_code==400,no_csrf.status_code
    response=session.post(base+f'/mi-comercio/productos/{product.id}/enviar',data={'csrf_token':csrf(tree)},timeout=25)
    assert response.status_code==200
    env.cr.rollback(); env.invalidate_all(); assert product.state=='pending'
    product.action_approve(); actuals |= product.product_tmpl_id; env.cr.commit()
    response, tree=get(session,'/mi-comercio/productos')
    assert 'Aprobado' in tree.text_content()
    response, tree=get(session,'/my')
    assert response.url.endswith('/mi-comercio') and 'PORTAL DE COMERCIOS' in tree.text_content()
    for path in ['/mi-comercio/productos', '/mi-comercio/stock', '/mi-comercio/pedidos']:
        response, tree=get(session,path)
        assert 'PORTAL DE COMERCIOS' in tree.text_content()
        assert 'Sus facturas' not in tree.text_content()
    response,tree=get(session,f'/mi-comercio/productos/{product.id}/stock')
    response=session.post(base+f'/mi-comercio/productos/{product.id}/stock',data={
        'csrf_token':csrf(tree),'stock_tracking':'1','stock_quantity':'12','available':'1'},timeout=25)
    assert response.status_code==200
    env.cr.rollback();env.invalidate_all()
    assert product.stock_quantity==12 and product.stock_tracking and product.state=='approved'
    response,tree=get(session,'/mi-comercio/stock')
    assert '12' in tree.text_content() and 'PRODUCTO WEB DE PRUEBA' in tree.text_content()
    assert sessions[1].get(base+f'/mi-comercio/productos/{product.id}/stock').status_code==404
    print('PASS: portal propio, secciones, ajuste de stock sin perder aprobación y aislamiento entre comercios')
    print('PASS: CSRF obligatorio, envío a revisión, aprobación y acceso desde Mi cuenta')
finally:
    env.cr.rollback()
    env.cr.rollback(); env.invalidate_all()
    stores = env['wah.merchant'].sudo().search([('owner_id','in',users.ids)])
    proposals=env['wah.merchant.product'].sudo().search([('merchant_id','in',stores.ids)])
    actuals |= proposals.mapped('product_tmpl_id')
    partners |= stores.mapped('partner_id')
    proposals.unlink()
    stores.unlink()
    actuals.sudo().unlink()
    users.sudo().unlink()
    partners.sudo().exists().unlink()
    env.cr.commit()
    print('Cuentas, locales y productos ficticios eliminados. No se enviaron invitaciones ni pedidos.')
