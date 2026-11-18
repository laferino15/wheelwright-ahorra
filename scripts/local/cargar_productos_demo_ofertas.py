"""Cinco productos de demostración en oferta; carga idempotente por código."""
from datetime import timedelta
import json
from pathlib import Path
from odoo import fields
assert env.cr.dbname == 'wheelwright_ahorra_dev'
website = env['website'].sudo().browse(1)
pricelist = website.pricelist_ids[:1]
assert pricelist and env['res.groups']._is_feature_enabled('product.group_product_pricelist')
items = [
    (9, 57, 'Milanesas de carne — bandeja de 750 g', 9000, 20),
    (10, 66, 'Facturas surtidas — docena', 8000, 25),
    (13, 72, 'Champú — 750 ml', 6500, 15),
    (14, 78, 'Lámpara LED 9 W — luz cálida', 3000, 30),
    (15, 84, 'Empanadas de carne — docena', 12000, 20),
]
results=[]
for sequence, (category_id, source_id, name, price, discount) in enumerate(items, 1):
    category=env['product.public.category'].sudo().browse(category_id).exists()
    assert category
    source=env['product.template'].sudo().browse(source_id).exists()
    assert source and source.image_1920 and category in source.public_categ_ids, (category_id,source_id)
    code='WA-DEMO-OFERTA-%s' % category_id
    product=env['product.template'].sudo().search([('default_code','=',code)],limit=1)
    store_name=category.name+' · Demostración'
    store=env['res.partner'].sudo().search([('name','=',store_name),('is_company','=',True)],limit=1)
    if not store:
        store=env['res.partner'].sudo().create({'name':store_name,'is_company':True,'city':'Wheelwright','country_id':env.ref('base.ar').id})
    if not product:
        product=env['product.template'].sudo().create({
            'name':name,'default_code':code,'type':'consu','sale_ok':True,'purchase_ok':False,
            'list_price':price,'taxes_id':[(5,0,0)],'public_categ_ids':[(6,0,category.ids)],
            'website_id':website.id,'is_published':True,'website_sequence':sequence*10,
            'image_1920':source.image_1920,'wah_store_id':store.id,'wah_catalog_sample':True,
            'description_sale':'Producto de demostración para visualizar ofertas. Precio de prueba e imagen ilustrativa; no representa una promoción comercial real.'})
    offer=env['wah.offer'].sudo().search([('product_id','=',product.id),('website_id','=',website.id)],limit=1)
    if not offer:
        offer=env['wah.offer'].sudo().create({'product_id':product.id,'website_id':website.id,
            'pricelist_id':pricelist.id,'discount':discount,'sequence':sequence*10,
            'date_start':fields.Datetime.now()-timedelta(minutes=5),'date_end':fields.Datetime.now()+timedelta(days=7)})
        offer.action_publish()
    assert offer.state=='published' and offer.rule_id
    actual=pricelist._compute_price_rule(product,1.0)[product.id]
    expected=product.list_price*(1-offer.discount/100)
    assert actual[1]==offer.rule_id.id and abs(actual[0]-expected)<.01
    results.append({'product_id':product.id,'name':product.name,'category':category.name,'before':product.list_price,'after':actual[0],'discount':offer.discount,'offer_id':offer.id})
env.cr.commit()
Path(r'C:/Users/LaferinoX/Desktop/wheelwright_actualizacion/productos_demo_ofertas.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(results,ensure_ascii=False))
