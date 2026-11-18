"""Regresión: confirmar COD sin generador PDF, sin enviar mensajes externos."""
from datetime import timedelta
import secrets
from unittest.mock import patch
from odoo import fields
assert env.cr.dbname == 'wheelwright_ahorra_dev'
try:
    site=env['website'].browse(1)
    merchant=env['wah.merchant'].sudo().search([('state','=','approved'),('owner_id.share','=',True)],limit=1)
    assert merchant
    product=env['product.template'].sudo().create({'name':'PRODUCTO FICTICIO PRUEBA PDF','type':'consu','sale_ok':True,'list_price':100,'wah_store_id':merchant.partner_id.id,'website_id':site.id})
    order=env['sale.order'].sudo().with_context(tracking_disable=True,send_email=False,mail_notrack=True).create({'partner_id':merchant.owner_id.partner_id.id,'website_id':site.id,'wah_delivery_date':fields.Date.today()+timedelta(days=1),'wah_delivery_window':'midday','order_line':[(0,0,{'product_id':product.product_variant_id.id,'product_uom_qty':1,'price_unit':100})]})
    provider=env['payment.provider'].sudo().search([('custom_mode','=','cash_on_delivery'),('state','=','enabled')],limit=1)
    tx=env['payment.transaction'].sudo().create({'provider_id':provider.id,'payment_method_id':provider.payment_method_ids[:1].id,'reference':'FICTICIO-PDF-'+secrets.token_hex(6),'amount':order.amount_total,'currency_id':order.currency_id.id,'partner_id':order.partner_id.id,'operation':'online_redirect','state':'pending','sale_order_ids':[(6,0,order.ids)]})
    with patch.object(type(env['ir.actions.report']),'get_wkhtmltopdf_state',lambda *a:'install'), patch.object(type(env['mail.mail']),'send',lambda *a,**k:True), patch.object(type(env['mail.mail']),'_send',lambda *a,**k:True), patch.object(type(env['ir.mail_server']),'send_email',side_effect=AssertionError('La prueba no debe enviar correos')):
        tx.with_context(tracking_disable=True,mail_notrack=True)._post_process()
    assert order.state=='sale' and tx.is_post_processed
    prep=order.wah_preparation_ids
    assert len(prep)==1 and prep.merchant_id==merchant and prep.state=='received'
    visible=env['wah.preparation'].with_user(merchant.owner_id).search([('id','=',prep.id)])
    assert visible and visible.read(['name','state','line_ids'])
    previous=prep.ids
    with patch.object(type(env['sale.order']),'_send_order_notification_mail',lambda *a,**k:None):
        tx._post_process()
    assert order.wah_preparation_ids.ids==previous
    template=order._get_confirmation_template()
    with patch.object(type(env['ir.actions.report']),'get_wkhtmltopdf_state',lambda *a:'install'):
        data=template.with_context(wah_optional_order_pdf=True)._generate_template_attachments(order.ids,['attachment_ids','report_template_ids'])
    assert data[order.id]['attachments']==[]
    assert data[order.id]['attachment_ids']==template.attachment_ids.ids
    print('PASS: confirmación COD sin PDF, preparación visible al dueño, sin duplicados y adjuntos estáticos conservados.')
finally:
    env.cr.rollback()
    print('Rollback completo. Sin pedidos ficticios persistidos ni correos enviados.')
