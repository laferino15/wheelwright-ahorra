"""Pruebas transaccionales: no conserva productos, pedidos ni cuentas."""
import secrets
from odoo.exceptions import AccessError, ValidationError
assert env.cr.dbname == 'wheelwright_ahorra_dev'

def denied(call, error=ValidationError):
    try:
        with env.cr.savepoint():
            call()
    except error:
        return
    raise AssertionError('La operación debía rechazarse')

try:
    token=secrets.token_hex(4)
    users=env['res.users'].sudo().with_context(no_reset_password=True,tracking_disable=True).create([
        {'name':'PRUEBA STOCK '+str(i),'login':f'stock-{token}-{i}@example.invalid','group_ids':[(6,0,env.ref('base.group_portal').ids)]} for i in range(3)])
    stores=env['wah.merchant'].sudo().create([
        {'name':'LOCAL STOCK '+str(i),'owner_id':users[i].id,'website_id':1,'category_id':9,'street':'FICTICIO','phone':'0000000'} for i in range(2)])
    stores.action_approve()
    offers=env['wah.merchant.product'].sudo().create([
        {'merchant_id':store.id,'name':'PRODUCTO STOCK '+str(i),'presentation':'bandeja de 500 g','category_id':9,'price':100,'image':env['product.template'].browse(59).image_1920,'stock_tracking':True,'stock_quantity':5,'state':'pending'} for i,store in enumerate(stores)])
    offers.action_approve()
    a=offers[0].with_user(users[0]); p=offers[0].product_tmpl_id
    a.action_update_stock(True,5,True)
    assert a.state=='approved' and p.website_published
    denied(lambda: a.action_update_stock(True,-1,True))
    denied(lambda: a.action_update_stock(True,'nan',True))
    denied(lambda: offers[1].with_user(users[0]).action_update_stock(True,1,True),AccessError)
    denied(lambda: a.write({'state':'approved'}),AccessError)
    a.action_update_stock(True,0,True); p.invalidate_recordset()
    assert p.wah_sold_out and p.website_published
    a.action_update_stock(True,5,False)
    assert a.state=='approved' and not p.website_published
    a.action_update_stock(True,5,True)
    assert a.state=='approved' and p.website_published
    print('PASS: ajuste de stock sin revisión, agotado visible, pausa/reactivación y aislamiento de dueños')

    def order(items):
        return env['sale.order'].sudo().with_context(tracking_disable=True,send_email=False,mail_notrack=True).create({
            'partner_id':users[2].partner_id.id,'website_id':1,
            'order_line':[(0,0,{'product_id':offer.product_tmpl_id.product_variant_id.id,'product_uom_qty':qty,'price_unit':100}) for offer,qty in items]})
    cart=order([(offers[0],1)])
    line=cart.order_line
    qty,warning=cart._verify_updated_quantity(line,p.product_variant_id.id,9,p.uom_id.id)
    assert qty==5 and warning
    assert a.stock_quantity==5
    bad=order([(offers[0],2),(offers[1],6)])
    denied(bad.action_confirm)
    assert all(x.stock_quantity==5 for x in offers) and bad.state=='draft'
    duplicate=order([(offers[0],3),(offers[0],3)])
    denied(duplicate.action_confirm)
    print('PASS: carrito limita cantidades sin reservar; pedidos mixtos y líneas duplicadas no exceden stock')

    sale=order([(offers[0],2)])
    sale.action_confirm()
    assert a.stock_quantity==3 and sale.order_line.wah_stock_reserved==2
    sale._wah_validate_stock(reserve=True)
    assert a.stock_quantity==3
    sale.action_cancel()
    assert a.stock_quantity==5 and sale.order_line.wah_stock_reserved==0
    sale.action_cancel()
    assert a.stock_quantity==5
    print('PASS: confirmación descuenta una vez; cancelación repone una sola vez')

    delivered=order([(offers[0],1)])
    delivered.action_confirm()
    prep=delivered.wah_preparation_ids
    prep.action_start(); prep.action_ready(); prep.action_collect(); prep.action_deliver()
    delivered.action_cancel()
    assert a.stock_quantity==4
    depleted=order([(offers[0],4)])
    depleted.action_confirm()
    assert a.stock_quantity==0
    denied(order([(offers[0],1)]).action_confirm)
    a.action_update_stock(False,0,True)
    unlimited=order([(offers[0],20)])
    unlimited.action_confirm()
    assert not unlimited.order_line.wah_stock_reserved
    print('PASS: lo entregado no se repone por cancelar; agotado bloquea y modo sin límite es explícito')
finally:
    env.cr.rollback()
    print('Pruebas revertidas: sin datos ficticios persistidos ni correos ni cobros.')
