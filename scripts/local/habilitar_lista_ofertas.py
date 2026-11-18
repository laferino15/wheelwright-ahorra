assert env.cr.dbname == 'wheelwright_ahorra_dev'
website = env['website'].sudo().browse(1)
pricelists = website.pricelist_ids
if not pricelists:
    pricelists = env['product.pricelist'].sudo().create({'name':'wheel-ahorra · Precios de tienda', 'currency_id':website.company_id.currency_id.id, 'company_id':website.company_id.id, 'website_id':website.id, 'selectable':False})
env.ref('base.group_user').sudo()._apply_group(env.ref('product.group_product_pricelist'))
assert env['res.groups']._is_feature_enabled('product.group_product_pricelist')
products = env['product.template'].sudo().search([('is_published','=',True),('sale_ok','=',True)])
prices = pricelists[:1]._compute_price_rule(products,1.0)
assert all(abs(prices[p.id][0] - p.list_price) < .001 for p in products), 'Revisar precios antes de activar'
env.cr.commit()
print('Lista de tienda habilitada. Precios de los productos conservados:',len(products))
