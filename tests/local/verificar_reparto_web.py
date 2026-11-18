"""RPC administrativo y portal de comprador con fixtures temporales."""
from datetime import timedelta
import secrets
import requests

assert env.cr.dbname=='wheelwright_ahorra_dev'
base='http://127.0.0.1:8070'
users=env['res.users'];partners=env['res.partner'];stores=env['wah.merchant'];products=env['product.template'];courier=env['wah.courier'];orders=env['sale.order']
sessions=[]
def refresh():
    env.cr.rollback();env.invalidate_all()
def rpc(session,model,method,args=None,kwargs=None,error=False):
    response=session.post(base+f'/web/dataset/call_kw/{model}/{method}',json={'jsonrpc':'2.0','method':'call','params':{'model':model,'method':method,'args':args or [],'kwargs':kwargs or {}},'id':1},timeout=35)
    assert response.status_code==200,response.status_code
    result=response.json()
    if error:
        assert 'error' in result,(model,method)
        return result
    assert 'error' not in result,result.get('error',{}).get('data',{}).get('message')
    return result.get('result')
try:
    token=secrets.token_hex(4)
    for i in range(3):
        password=secrets.token_urlsafe(24)
        groups=[env.ref('base.group_user').id,env.ref('product.group_product_manager').id,env.ref('sales_team.group_sale_manager').id] if i==0 else env.ref('base.group_portal').ids
        user=env['res.users'].sudo().with_context(no_reset_password=True,tracking_disable=True).create({'name':f'FICTICIO RUTA WEB {i}','login':f'ruta-web-{token}-{i}@example.invalid','password':password,'group_ids':[(6,0,groups)]})
        users|=user;partners|=user.partner_id;env.cr.commit()
        session=requests.Session();session.trust_env=False
        auth=session.post(base+'/web/session/authenticate',json={'jsonrpc':'2.0','method':'call','params':{'db':env.cr.dbname,'login':user.login,'password':password},'id':1},timeout=25).json()
        assert auth.get('result',{}).get('uid')==user.id
        sessions.append(session)
    stores=env['wah.merchant'].sudo().create({'name':'LOCAL RUTA WEB FICTICIO','owner_id':users[1].id,'website_id':1,'category_id':9,'street':'FICTICIO','phone':'000000'})
    stores.action_approve();partners|=stores.partner_id
    products=env['product.template'].sudo().create({'name':'PRODUCTO RUTA WEB FICTICIO','type':'consu','list_price':100,'image_1920':env['product.template'].browse(59).image_1920,'wah_store_id':stores.partner_id.id,'website_id':1})
    courier=env['wah.courier'].sudo().create({'name':'REPARTIDOR FICTICIO WEB','phone':'000000'})
    orders=env['sale.order'].sudo().with_context(send_email=False,tracking_disable=True,mail_notrack=True).create({'partner_id':users[2].partner_id.id,'website_id':1,'wah_delivery_date':env['sale.order']._wah_local_now().date()+timedelta(days=1),'wah_delivery_window':'afternoon','order_line':[(0,0,{'product_id':products.product_variant_id.id,'product_uom_qty':1,'price_unit':100})]})
    orders.action_confirm();orders.wah_preparation_ids.action_start();orders.wah_preparation_ids.action_ready();env.cr.commit()
    admin,buyer=sessions[0],sessions[2]
    response=admin.get(base+'/odoo',timeout=35);assert response.status_code==200
    views=rpc(admin,'sale.order','get_views',kwargs={'views':[(env.ref('wheelwright_ahorra.dispatch_form').id,'form'),(env.ref('wheelwright_ahorra.dispatch_list').id,'list')],'options':{'toolbar':True}})
    assert 'action_wah_dispatch' in views['views']['form']['arch']
    assert 'action_wah_collection_wizard' in views['views']['form']['arch']
    rpc(buyer,'sale.order','action_wah_dispatch',[[orders.id]],error=True)
    rpc(admin,'sale.order','write',[[orders.id],{'wah_courier_id':courier.id}])
    rpc(admin,'sale.order','action_wah_assign',[[orders.id]])
    rpc(admin,'sale.order','action_wah_dispatch',[[orders.id]],error=True)
    rpc(admin,'wah.preparation','action_collect',[orders.wah_preparation_ids.ids])
    rpc(admin,'sale.order','action_wah_dispatch',[[orders.id]])
    response=buyer.get(base+f'/my/orders/{orders.id}',timeout=35)
    assert response.status_code==200 and 'En camino' in response.text and 'Pendiente de cobro' in response.text
    rpc(admin,'sale.order','action_wah_deliver',[[orders.id]])
    refresh();assert orders.wah_collection_state=='pending'
    total=orders.amount_total
    wiz=rpc(admin,'wah.collection.register','create',[{'order_id':orders.id,'amount':total,'received_amount':total+100,'method':'cash'}])
    wiz=wiz[0] if isinstance(wiz,list) else wiz
    result=rpc(admin,'wah.collection.register','action_register',[[wiz]])
    refresh();receipt=env['wah.collection'].sudo().browse(result['res_id'])
    assert receipt.amount==total and receipt.change_amount==100 and receipt.actor_id==users[0]
    rpc(admin,'wah.collection.register','action_register',[[wiz]],error=True)
    rpc(buyer,'wah.collection','read',[[receipt.id],['amount']],error=True)
    response=buyer.get(base+f'/my/orders/{orders.id}',timeout=35)
    assert response.status_code==200 and 'Entregado' in response.text and 'Cobro registrado' in response.text
    assert 'REPARTIDOR FICTICIO WEB' not in response.text and receipt.name not in response.text
    refresh();assert len(orders.wah_collection_ids)==1 and orders.wah_route_state=='delivered'
    assert not orders.transaction_ids
    print('PASS: vistas administrativas y RPC reales, permisos, retiros, reparto, entrega y cobro separado con vuelto')
    print('PASS: cliente ve En camino, Entregado y Cobro registrado; no ve el registro interno ni el repartidor')
finally:
    refresh()
    if orders.exists():
        # Solo nuestros fixtures: restablecer banderas para limpiar sin dejar pedidos ficticios.
        orders.wah_collection_ids.sudo().unlink()
        orders.sudo().write({'wah_route_state':'pending'})
        orders.wah_preparation_ids.sudo().write({'state':'ready'})
        pickings=orders.picking_ids
        orders.action_unlock();orders.action_cancel()
        orders.wah_preparation_ids.sudo().unlink();pickings.sudo().unlink()
        orders.wah_route_event_ids.sudo().unlink();orders.sudo().unlink()
    products.sudo().exists().unlink();stores.sudo().exists().unlink();courier.sudo().exists().unlink()
    users.sudo().exists().unlink();partners.sudo().exists().unlink();env.cr.commit()
    print('Fixtures eliminados. Sin cobros reales, correos ni asientos contables.')
