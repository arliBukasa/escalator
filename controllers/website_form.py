from odoo import http
from odoo.addons.website_form.controllers.main import WebsiteForm
from odoo.http import request
import logging


class ContactController(WebsiteForm):

    @http.route('/website_form/<string:model_name>', type='http', auth="public", methods=['POST'], website=True)
    def website_form(self, model_name, **kwargs):
        if model_name == 'escalator_lite.ticket':
            if request.session.uid:
                request.params['partner_id'] = request.env.user.partner_id.id
                request.params['email_from'] = request.env.user.partner_id.email
                kwargs['partner_id'] = request.env.user.partner_id.id
                kwargs['email_from'] = request.env.user.partner_id.email

                logging.info('============================ Partner ID: %s,%s,%s', request.env.user.partner_id.id,request.env.user.partner_id.name,request.env.user.partner_id.email)
                logging.info('============================ Parametres: %s', request.params)
                logging.info('============================ Kwargs:')
                logging.info(kwargs)

        return super(ContactController, self).website_form(model_name, **kwargs)
# 