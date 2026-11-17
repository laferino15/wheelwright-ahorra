assert env.cr.dbname=='wheelwright_ahorra_dev'
cancelled=env['sale.order'].sudo().with_context(tracking_disable=True).search([('website_id','!=',False),('state','=','cancel')])
cancelled.filtered(lambda order:order.wah_route_state=='pending').write({'wah_route_state':'cancelled'})
cancelled._compute_wah_collection()
env.cr.commit()
print('Pedidos cancelados anteriores reconocidos:',len(cancelled))
print('No se asignaron repartidores ni se registraron cobros históricos.')
