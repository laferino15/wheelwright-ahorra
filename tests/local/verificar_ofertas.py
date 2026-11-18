"""Ofertas reales sobre reglas nativas; toda la transacción se revierte."""
from datetime import timedelta
from types import SimpleNamespace
from werkzeug.wrappers import Request as HttpRequest
from odoo import fields
from odoo.http import _request_stack
from odoo.exceptions import AccessError, ValidationError
assert env.cr.dbname == 'wheelwright_ahorra_dev'
class Session(dict):
    debug = ''

def denied(call, error=ValidationError):
    try:
        with env.cr.savepoint():
            call()
    except error:
        return
    raise AssertionError('La operación debía ser rechazada')

try:
    website=env['website'].browse(1)
    manager=env.ref('base.user_admin')
    public=env.ref('base.public_user')
    pricelist=website.pricelist_ids[:1] or env['product.pricelist'].sudo().create({'name':'LISTA FICTICIA OFERTAS','currency_id':website.company_id.currency_id.id,'company_id':website.company_id.id,'website_id':website.id})
    product=env['product.template'].sudo().create({'name':'OFERTA FICTICIA NO PUBLICAR','list_price':1000,'sale_ok':True,'is_published':True,'website_id':website.id,'taxes_id':[(5,0,0)]})
    values={'product_id':product.id,'website_id':website.id,'pricelist_id':pricelist.id,'discount':20,'date_start':fields.Datetime.now()-timedelta(days=1),'date_end':fields.Datetime.now()+timedelta(days=1)}
    Offer=env['wah.offer'].with_user(manager)
    offer=Offer.create(values)
    assert offer.state=='draft' and not offer.rule_id
    denied(lambda: env['wah.offer'].with_user(public).create(values),AccessError)
    denied(lambda: offer.with_user(public).read(['discount']),AccessError)
    denied(lambda: offer.write({'discount':0}))
    denied(lambda: offer.write({'discount':100}))
    denied(lambda: offer.write({'state':'published'}),AccessError)
    offer.action_publish()
    rule=offer.rule_id
    price,rule_id=pricelist._compute_price_rule(product,1.0)[product.id]
    assert price==800 and rule_id==rule.id,(price,rule_id)
    denied(lambda: offer.write({'discount':50}))
    duplicate=Offer.create(values);denied(duplicate.action_publish)
    print('PASS: descuento nativo 20 %, permisos, condiciones protegidas y duplicados bloqueados')
    mock=SimpleNamespace(pricelist=pricelist,fiscal_position=env['account.fiscal.position'],website=website,env=env,session=Session(),cookies={},is_frontend=True,cart=env['sale.order'],httprequest=HttpRequest.from_values(path='/ofertas',base_url='http://127.0.0.1:8070'))
    _request_stack.push(mock)
    try:
        cards=website.with_user(public)._wah_offer_cards()
        card=next(c for c in cards if c['product'].id==product.id)
        assert card['previous']==1000 and card['current']==800 and card['saving']==200 and card['discount_label']=='20%',card
        rendered=env['ir.ui.view']._render_template('wheelwright_ahorra.offer_cards',{'offer_cards':[card],'website':website})
        assert '20%' in str(rendered) and 'Ahorrás' in str(rendered)
        # El mismo precio se calcula al crear una línea del pedido con esa lista.
        order=env['sale.order'].sudo().with_context(tracking_disable=True,send_email=False).create({'partner_id':public.partner_id.id,'website_id':website.id,'pricelist_id':pricelist.id,'order_line':[(0,0,{'product_id':product.product_variant_id.id,'product_uom_qty':1})]})
        assert order.order_line.price_unit==800,order.order_line.price_unit
        print('PASS: precio anterior, ahorro y descuento coinciden con el precio del pedido')
        offer.action_pause()
        assert not rule.exists() and not offer.rule_id
        assert not any(c['product'].id==product.id for c in website.with_user(public)._wah_offer_cards())
        assert pricelist._compute_price_rule(product,1.0)[product.id][0]==1000
        print('PASS: pausar retira la oferta y restaura el precio nativo')
        offer.write({'date_start':fields.Datetime.now()+timedelta(days=2),'date_end':fields.Datetime.now()+timedelta(days=3)})
        offer.action_publish()
        assert not any(c['product'].id==product.id for c in website.with_user(public)._wah_offer_cards())
        offer.action_pause()
        offer.write({'date_start':fields.Datetime.now()-timedelta(days=2),'date_end':fields.Datetime.now()-timedelta(days=1)})
        denied(offer.action_publish)
        print('PASS: ofertas futuras ocultas y ofertas vencidas no publicables')
    finally:
        _request_stack.pop()
    print('RESULTADO: OFERTAS APROBADAS')
finally:
    env.cr.rollback()
    print('Rollback completo: sin productos ni promociones ficticias persistidos.')
