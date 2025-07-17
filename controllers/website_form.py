from odoo import http, _
from odoo.http import request
import logging
import base64
from datetime import datetime
import re
# from odoo.addons.website_form.controllers.main import WebsiteForm

class EscalatorWebsiteForm(http.Controller):

    def _parse_date(self, date_str):
        """Parse date string from various formats and return ISO format"""
        if not date_str:
            return None
        
        # Nettoyer la chaîne
        date_str = date_str.strip()
        
        # Formats possibles
        formats = [
            '%Y-%m-%d',        # ISO format (YYYY-MM-DD)
            '%d/%m/%Y',        # French format (DD/MM/YYYY)
            '%m/%d/%Y',        # US format (MM/DD/YYYY)
            '%d-%m-%Y',        # Alternative format (DD-MM-YYYY)
            '%m-%d-%Y',        # Alternative format (MM-DD-YYYY)
            '%Y/%m/%d',        # Alternative format (YYYY/MM/DD)
            '%d.%m.%Y',        # European format (DD.MM.YYYY)
            '%Y-%m-%d %H:%M:%S',  # With time
            '%d/%m/%Y %H:%M:%S',  # French with time
            '%m/%d/%Y %H:%M:%S',  # US with time
        ]
        
        for fmt in formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                # Retourner au format ISO
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        # Si aucun format ne fonctionne, essayer de détecter automatiquement
        try:
            # Regex pour détecter les formats courants
            if re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', date_str):
                parts = date_str.split('/')
                day, month, year = parts[0], parts[1], parts[2]
                
                # Vérifier si c'est MM/DD/YYYY ou DD/MM/YYYY
                if int(month) > 12:  # Si mois > 12, c'est DD/MM/YYYY
                    day, month = month, day
                elif int(day) > 12:  # Si jour > 12, c'est MM/DD/YYYY
                    month, day = day, month
                
                # Créer la date
                parsed_date = datetime(int(year), int(month), int(day))
                return parsed_date.strftime('%Y-%m-%d')
                
        except (ValueError, IndexError):
            pass
        
        logging.warning('Impossible de parser la date: %s', date_str)
        return None

    def _normalize_form_data(self, fields):
        """Normalise les données du formulaire"""
        # Normaliser les dates
        if 'date_deadline' in fields and fields['date_deadline']:
            normalized_date = self._parse_date(fields['date_deadline'])
            if normalized_date:
                fields['date_deadline'] = normalized_date
            else:
                # Supprimer la date si elle ne peut pas être parsée
                del fields['date_deadline']
                logging.warning('Date deadline invalide supprimée')
        
        return fields

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

                # Normaliser les données du formulaire (notamment les dates)
                fields = self._normalize_form_data(fields)
                
                logging.info('============================ Champs après normalisation: %s', fields)

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
                return request.redirect('/escalator/success?ticket_id=' + str(ticket.id))
                
            except Exception as e:
                logging.error('Erreur lors de la création du ticket: %s', str(e))
                return request.redirect('/escalator/error?message=' + str(e))

    
    @http.route('/escalator/success', type='http', auth="public", website=True)
    def ticket_success(self, ticket_id=None):
        """Page de succès après création de ticket"""
        values = {
            'ticket_id': ticket_id,
            'message': 'Your ticket has been created successfully!'
        }
        return request.render("escalator.ticket_success", values)
    
    @http.route('/escalator/error', type='http', auth="public", website=True)
    def ticket_error(self, message=None):
        """Page d'erreur"""
        values = {
            'error_message': message or 'An error occurred while creating your ticket.'
        }
        return request.render("escalator.ticket_error", values)
