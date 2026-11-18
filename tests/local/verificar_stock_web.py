"""Formulario real, carrito nativo y dos confirmaciones concurrentes; fixtures eliminados."""
import secrets
from concurrent.futures import ThreadPoolExecutor
import requests
from lxml import html
from odoo import api, SUPERUSER_ID
from odoo.exceptions import ValidationError
from psycopg2.errors import SerializationFailure, DeadlockDetected

assert env.cr.dbname=='wheelwright_ahorra_dev'
base='http://127.0.0.1:8070'
users=env['res.users']; stores=env['wah.merchant']; offers=env['wah.merchant.product']; actuals=env['product.template']; partners=env['res.partner']
sessions=[]
def refresh():
    env.cr.rollback(); env.invalidate_all()
def get(session,path,status=200):
    response=session.get(base+path,timeout=30)
    assert response.status_code==status,(path,response.status_code)
    return response,html.fromstring(response.content)
def csrf(tree):
    return tree.xpath('//input[@name="csrf_token"]/@value')[0]
try:
    token=secrets.token_hex(4)
    for i in range(3):
        password=secrets.token_urlsafe(24)
        user=env['res.users'].sudo().with_context(no_reset_password=True,tracking_disable=True).create({
            'name':f'PRUEBA STOCK WEB {i}','login':f'stock-web-{token}-{i}@example.invalid','password':password,
            'group_ids':[(6,0,env.ref('base.group_portal').ids)]})
        users|=user; partners|=user.partner_id; env.cr.commit()
        session=requests.Session(); session.trust_env=False
        result=session.post(base+'/web/session/authenticate',json={'jsonrpc':'2.0','method':'call','params':{'db':env.cr.dbname,'login':user.login,'password':password},'id':1},timeout=25).json()
        assert result.get('result',{}).get('uid')==user.id
        sessions.append(session)
    stores=env['wah.merchant'].sudo().create([{'owner_id':users[i].id,'name':f'LOCAL FICTICIO STOCK {i}', 'website_id':1,'category_id':9,'street':'FICTICIO','phone':'000000'} for i in range(2)])
    stores.action_approve(); partners|=stores.partner_id
    offers=env['wah.merchant.product'].sudo().create([{'merchant_id':store.id,'name':f'PRODUCTO FICTICIO STOCK {i}','category_id':9,'presentation':'unidad','price':100,'image':env['product.template'].browse(59).image_1920,'stock_tracking':True,'stock_quantity':2,'state':'pending'} for i,store in enumerate(stores)])
    offers.action_approve(); actuals=offers.product_tmpl_id
    env.cr.commit()
    own=offers[0]; product=own.product_tmpl_id; seller=sessions[0]; buyer=sessions[2]
    response,tree=get(seller,'/mi-comercio')
    assert 'Ajustar stock' in response.text
    response,tree=get(seller,'/mi-comercio/productos/nuevo')
    assert tree.xpath('//input[@name="stock_tracking"]')
    path=f'/mi-comercio/productos/{own.id}/stock'
    response,tree=get(seller,path)
    stock_token=csrf(tree)
    get(sessions[1],path,404); get(buyer,path,404)
    assert seller.post(base+path,data={'stock_quantity':'1'},timeout=25).status_code==400
    response=seller.post(base+path,data={'csrf_token':stock_token,'stock_tracking':'1','stock_quantity':'-1','available':'1'},timeout=25)
    assert response.status_code==200 and 'mayor o igual a cero' in response.text
    refresh(); assert own.stock_quantity==2 and own.state=='approved'
    response=seller.post(base+path,data={'csrf_token':stock_token,'stock_tracking':'1','stock_quantity':'0','available':'1'},timeout=25)
    assert response.status_code==200 and 'actualizaron' in response.text
    refresh(); assert own.stock_quantity==0 and own.state=='approved' and product.website_published
    response,tree=get(buyer,product.website_url)
    assert 'agotado por el momento' in response.text
    assert 'disabled' in tree.xpath('//a[@id="add_to_cart"]/@class')[0]
    print('PASS: formulario, CSRF, validación, aislamiento y producto agotado con botón deshabilitado')
    seller.post(base+path,data={'csrf_token':stock_token,'stock_tracking':'1','stock_quantity':'2','available':'1'},timeout=25)
    refresh(); assert own.stock_quantity==2
    result=buyer.post(base+'/shop/cart/add',json={'jsonrpc':'2.0','method':'call','params':{'product_template_id':product.id,'product_id':product.product_variant_id.id,'quantity':3},'id':2},timeout=30).json()
    assert 'error' not in result,result.get('error',{}).get('data',{}).get('message')
    refresh()
    carts=env['sale.order'].sudo().search([('partner_id','=',users[2].partner_id.id),('website_id','=',1)])
    assert len(carts)==1 and carts.order_line.product_uom_qty==2 and own.stock_quantity==2
    print('PASS: carrito nativo limita la compra a dos unidades sin descontar existencias')

    own.action_update_stock(True,1,True)
    race=env['sale.order'].sudo().with_context(tracking_disable=True,send_email=False,mail_notrack=True).create([
        {'partner_id':users[2].partner_id.id,'website_id':1,'order_line':[(0,0,{'product_id':product.product_variant_id.id,'product_uom_qty':1,'price_unit':100})]} for _ in range(2)])
    ids=race.ids; registry=env.registry
    env.cr.commit()
    def confirm(order_id):
        for retry in range(4):
            with registry.cursor() as cr:
                thread_env=api.Environment(cr,SUPERUSER_ID,{'tracking_disable':True,'send_email':False,'mail_notrack':True})
                try:
                    thread_env['sale.order'].browse(order_id).action_confirm(); cr.commit()
                    return 'confirmed'
                except ValidationError:
                    cr.rollback(); return 'blocked'
                except (SerializationFailure,DeadlockDetected):
                    cr.rollback()
        raise AssertionError('No se resolvió la concurrencia')
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(confirm,ids))
    refresh()
    assert sorted(results)==['blocked','confirmed'] and own.stock_quantity==0,results
    print('PASS: dos compras simultáneas por la última unidad: solo una confirmada')
finally:
    refresh()
    if users:
        orders=env['sale.order'].sudo().search([('partner_id','in',users.partner_id.ids)])
        if orders:
            pickings=orders.picking_ids
            orders.action_unlock(); orders.action_cancel()
            orders.wah_preparation_ids.unlink(); pickings.unlink(); orders.unlink()
    offers.sudo().exists().unlink()
    actuals.sudo().exists().unlink()
    stores.sudo().exists().unlink()
    users.sudo().exists().unlink()
    partners.sudo().exists().unlink()
    env.cr.commit()
    print('Fixtures eliminados; no se enviaron correos ni se registraron cobros.')
