from odoo import http, _
from odoo.http import request
import logging
import base64
# from odoo.addons.website_form.controllers.main import WebsiteForm

class EscalatorWebsiteForm(http.Controller):

    @http.route('/escalator/create/<string:model_name>', type='http', auth="public", methods=['POST'], website=True, csrf=False)
    def create(self, model_name, **kwargs):
        if model_name == 'escalator_lite.ticket':
            try:
                # Ajouter des logs pour déboguer
                logging.info('============================ Création ticket - Request Params: %s', request.params)
                
                # Préparer les données pour la création du ticket
                fields = kwargs.copy()
                
                # Nettoyer les champs qui ne doivent pas être dans la création
                fields_to_remove = ['csrf_token', 'attachment', 'Attachment']
                for field in fields_to_remove:
                    if field in fields:
                        del fields[field]

                # Créer le ticket
                ticket = request.env['escalator_lite.ticket'].sudo().create(fields)
                
                # Traiter l'attachment séparément si présent
                attachment_file = None
                if 'Attachment' in request.httprequest.files:
                    attachment_file = request.httprequest.files['Attachment']
                elif 'attachment' in request.httprequest.files:
                    attachment_file = request.httprequest.files['attachment']

                if attachment_file and attachment_file.filename:
                    ticket.message_post(
                        body=_('Attachment: %s') % attachment_file.filename,
                        attachment_ids=[(0, 0, {
                            'name': attachment_file.filename,
                            'datas': base64.b64encode(attachment_file.read()),
                            'datas_fname': attachment_file.filename,
                        })]
                    )
                
                logging.info('============================ Ticket créé avec ID : %s', ticket.id)
                logging.info('============================ Redirection vers la page de succès: ticket_id=%s', ticket.id)
                
                # Retourner une redirection vers la page de succès
                #return request.env['ir.ui.view'].render_template("escalator.ticket_thanks", {"ticket_id": ticket.id})
                return request.render("escalator.ticket_thanks", {"ticket_id": ticket.id})
                
            except Exception as e:
                logging.error('Erreur lors de la création du ticket: %s', str(e))
                return request.render("escalator.ticket_error", {"error_message": str(e)})

    
    @http.route('/escalator/success', type='http', auth="public", website=True)
    def ticket_success(self, ticket_id=None):
        """Page de succès après création de ticket"""
        values = {
            'ticket_id': ticket_id,
            'message': 'Your ticket has been created successfully!'
        }
        return request.env['ir.ui.view'].render_template("escalator.ticket_success", values)
    
    @http.route('/escalator/error', type='http', auth="public", website=True)
    def ticket_error(self, message=None):
        """Page d'erreur"""
        values = {
            'error_message': message or 'An error occurred while creating your ticket.'
        }
        return request.env['ir.ui.view'].render_template("escalator.ticket_error", values)
