from odoo import http
from odoo.http import request
import logging

class ContactController(http.Controller):  # Assurez-vous d'étendre http.Controller si ce n'est pas un sous-contrôleur.

    @http.route('/website_form/<string:model_name>', type='http', auth="public", methods=['POST'], website=True)
    def website_form(self, model_name, contact_name="", email_from="", **kwargs):
        if model_name == 'escalator_lite.ticket':
            # Ajouter des logs pour déboguer
            logging.info('============================ Request Params: %s', request.params)
            logging.info('============================ Email From: %s', email_from)
            logging.info('============================ Contact Name: %s', contact_name)

            # Ajouter les valeurs des champs personnalisés dans kwargs
            if email_from:
                kwargs['email_from'] = email_from
            if contact_name:
                kwargs['contact_name'] = contact_name
            
            logging.info('============================ Kwargs avant création: %s', kwargs)

            # Créer un nouvel enregistrement
            try:
                fields = kwargs.copy()  # Copie pour éviter des problèmes si d'autres champs sont modifiés
                if 'attachment' in fields:
                    attachment = request.httprequest.files['attachment']
                    del fields['attachment']  # Supprimer avant la création du ticket
                else:
                    attachment = None

                ticket = request.env['escalator_lite.ticket'].sudo().create(fields)

                # Ajouter un message pour les pièces jointes
                if attachment:
                    ticket.message_post(
                        body=_('Attachment: %s') % attachment.filename,
                        attachment_ids=[(0, 0, {
                            'name': attachment.filename,
                            'datas': attachment.read(),
                            'datas_fname': attachment.filename,
                        })]
                    )
                # Renvoyer la page de succès
                return request.render('escalator.ticket_thanks', {})
            except Exception as e:
                logging.error('Erreur lors de la création du ticket: %s', str(e))
                return request.render('escalator.ticket_error', {'error': str(e)})

        return super(ContactController, self).website_form(model_name, **kwargs)
