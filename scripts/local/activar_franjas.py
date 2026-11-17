assert env.cr.dbname=='wheelwright_ahorra_dev'
website=env['website'].sudo().browse(1)
assert website.wah_local_checkout
website.write({'wah_delivery_windows_enabled':True})
env.cr.commit()
print('Franjas activadas para wheel-ahorra local.')
