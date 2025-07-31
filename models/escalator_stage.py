# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import re
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta
import pytz


class Stage(models.Model):
    """ Model for case stages. This models the main stages of a document
        management flow. Tickets will now use only stages, instead of state and stages.
        Stages are for example used to display the kanban view of records.
    """
    _name = "escalator.stage"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Stage of case"
    _rec_name = 'name'
    _order = "sequence, name, id"

    name = fields.Char('Stage Name', required=True, translate=True)
    sequence = fields.Integer('Sequence', default=1, help="Used to order stages. Lower is better.")
    requirements = fields.Text('Requirements', help="Enter here the internal requirements for this stage (ex: Offer sent to customer). It will appear as a tooltip over the stage's name.")
    fold = fields.Boolean('Folded in Pipeline',
        help='This stage is folded in the kanban view when there are no records in that stage to display.')
    legend_blocked = fields.Char(
        string='Kanban Blocked Explanation', translate=True,
        help='Override the default value displayed for the blocked state for kanban selection, when the ticket is in that stage.')
    legend_done = fields.Char(
        string='Kanban Done Explanation', translate=True,
        help='Override the default value displayed for the done state for kanban selection, when the ticket is in that stage.')
    legend_normal = fields.Char(
        string='Kanban Normal Explanation', translate=True,
        help='Override the default value displayed for the normal state for kanban selection, when the ticket is in that stage.')
    last = fields.Boolean('Last in Pipeline',
        help='This stage is last for closed tickets.')

class HrExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"
    
    date_to_approve=fields.Date(string="date limite pour l'approbation du manager")
    date_to_finace_approve=fields.Date(string="date limite pour l'approbation de finance")
    date_to_dg_approve=fields.Date(string="date limite pour l'approbation du DG")
    date_to_paie=fields.Date(string="date limite de paiement")
    paiement_date=fields.Date(string="Date de paiement prevue")
    
    tickect_ids = fields.One2many(
        string='tickects',
        comodel_name='escalator_lite.ticket',
        inverse_name='expense_sheet_id',
    )
    numero=fields.Char(string="Num of expense", default="/")
        
    def notification_ticket(self, user, message_texte):
        """Send notification email to user
        
        Args:
            user (res.users): User to notify
            message_texte (str): HTML message content
        """
        try:
            # Use Odoo mail.mail for better email handling
            mail_values = {
                'subject': _("Warning for Untreated Task"),
                'email_to': user.employee_id.work_email,
                'email_cc': user.employee_id.work_email,
                'body_html': message_texte,
                'email_from': self.env['ir.mail_server'].sudo()._get_default_from_address() or 'notifications@example.com',
            }
            self.env['mail.mail'].sudo().create(mail_values).send()
            
            _logger.info("Notification sent to %s", user.employee_id.name)
            
        except Exception as e:
            _logger.error("Failed to send notification email: %s", str(e), exc_info=True)
            raise UserError(_("Failed to send notification email: %s") % str(e))
    @api.model
    def create(self, vals):
        # Set default sequence if not provided
        if vals.get('numero', '/') == '/':
            vals['numero'] = self.env['ir.sequence'].next_by_code('expense.sequence') or '/'
        
        # Call super with updated values
        expense = super(HrExpenseSheet, self).create(vals)
        return expense

    def write(self, vals):
        if "state" in vals:
            today = fields.Date.context_today(self)
            for hexpense in self:
                if vals['state'] == 'submit':
                    _logger.debug("Processing state change to 'submit'")
                    hexpense.date_to_approve = today + timedelta(days=1)
                elif vals['state'] == 'approve':
                    _logger.debug("Processing state change to 'approve'")
                    hexpense.date_to_finace_approve = today + timedelta(days=1)
                elif vals['state'] == 'approve1':
                    hexpense.date_to_dg_approve = today + timedelta(days=1)
                elif vals['state'] == 'approve2':
                    if hexpense.paiement_date:
                        hexpense.date_to_paie=hexpense.paiement_date
                    else:
                        hexpense.date_to_paie=datetime.date.today()+datetime.timedelta(days=1)
                        
        res = super(HrExpenseSheet, self).write(vals)
                        
    @api.multi
    def _ticket_generator(self):
        logging.info("=======je suis dans la racine du generateur des tickets======")
        logging.info(self)
        for users in self.env["res.users"].search([]):             
            if users.has_group("hrms_dashboard.group_hrms_dashboard_dg"):
                user=users
                for expense in self.env["hr.expense.sheet"].search([]):
                    
                    logging.info("=======je suis dans le generateur des tickets======")
                    logging.info(expense)
                    
                    if expense.state=="submit":
                        logging.info("=======generateur des tickets: verification des etats (submit)======")
                        logging.info(expense.state)
                        logging.info("=======comparaison des dates======")
                        logging.info(expense.date_to_approve==datetime.date.today()-datetime.timedelta(days=1))
                        logging.info(expense.date_to_approve)
                        logging.info(datetime.date.today()-datetime.timedelta(days=1))
                        if expense.date_to_approve==datetime.datetime.today()-datetime.timedelta(days=1):
                            vals={
                                "name":"warning, for an untreated requisition",
                                "description":"the agent has submitted a requisition for more than 24 hours, he is waiting for the manager's approval, this is the requisition number:"+expense.numero,
                                "employee_id":expense.employee_id.id,
                                "user_id":user.id,
                                "date_deadline":datetime.date.today()+datetime.timedelta(days=1),
                                "expense_sheet_id":expense.id,
                                "color":3,
                                }
                            self.env["escalator_lite.ticket"].create(vals)
                            message_texte=str("Hi "+user.employee_id.name+"!<br> the system generated a ticket, for an untreated requisition!(need line approval),this is the requisition number:"+expense.numero)
                            logging.info("=======ticket à notifier======")
                            logging.info(expense)                             
                            expense.notification_ticket(user,message_texte)
                              
                    if expense.state=="approve":
                            logging.info("=======generateur des tickets: verification des etats (approve)======")
                            logging.info(expense.state)
                            logging.info("=======comparaison des dates======")
                            logging.info(expense.date_to_approve==datetime.date.today()-datetime.timedelta(days=1))
                            logging.info(expense.date_to_approve)
                            logging.info(datetime.date.today()-datetime.timedelta(days=1))
                                
                            if expense.date_to_approve==datetime.date.today()-datetime.timedelta(days=1):
                                vals={
                                    "name":"warning, for an untreated requisition",
                                    "description":"the manager has approved a requisition for more than 24 hours, he is waiting for the finance approval, this is the requisition number:"+expense.numero,
                                    "employee_id":expense.employee_id.id,
                                    "user_id":user.id,
                                    "date_deadline":datetime.date.today()+datetime.timedelta(days=1),
                                    "expense_sheet_id":expense.id,
                                    "color":5,
                                }
                                self.env["escalator_lite.ticket"].create(vals)
                                message_texte=str("Hi "+user.employee_id.name+"!<br> the system generated a ticket, for an untreated requisition!(need finance approval), this is the requisition number:"+expense.numero)
                                logging.info("=======ticket à notifier======")
                                logging.info(self)
                                logging.info("=======ticket à notifier======")
                                logging.info(expense)                             
                                expense.notification_ticket(user,message_texte)
                    if expense.state=="approve1":
                            logging.info("=======generateur des tickets: verification des etats (approve1)======")
                            logging.info(expense.state)
                            logging.info("=======comparaison des dates======")
                            logging.info(expense.date_to_approve==datetime.date.today()-datetime.timedelta(days=1))
                            logging.info(expense.date_to_approve)
                            logging.info(datetime.date.today()-datetime.timedelta(days=1))
                                
                            if expense.date_to_approve==datetime.date.today()-datetime.timedelta(days=1):
                                vals={
                                    "name":"warning, for an untreated requisition",
                                    "description":"finance approved, resuisition 24 hours ago, it is still pending MD approval, this is the requisition number:"+expense.numero,
                                    "employee_id":expense.employee_id.id,
                                    "user_id":user.id,
                                    "date_deadline":datetime.date.today()+datetime.timedelta(days=1),
                                    "expense_sheet_id":expense.id,
                                    "color":4,
                                }
                                self.env["escalator_lite.ticket"].create(vals)
                                message_texte=str("Hi "+user.employee_id.name+"!<br> the system generated a ticket, for an untreated requisition!(need your approval), this is the requisition number:"+expense.numero)
                                logging.info("=======ticket à notifier======")
                                logging.info(self) 
                                logging.info("=======ticket à notifier======")
                                logging.info(expense)                             
                                expense.notification_ticket(user,message_texte)