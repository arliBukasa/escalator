# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, SUPERUSER_ID, _
import re
from odoo.exceptions import AccessError
import datetime
import pytz
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
AVAILABLE_PRIORITIES = [
    ('0', 'Low'),
    ('1', 'Normal'),
    ('2', 'High'),
    ('3', 'Urgent'),
]


class escalatorTicket(models.Model):
    _name = "escalator_lite.ticket"
    _description = "escalator Tickets"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = "priority desc, create_date desc"
    _mail_post_access = 'read'

    @api.model
    def _get_default_stage_id(self):
        return self.env['escalator_lite.stage'].search([], order='sequence', limit=1)

    name = fields.Char(string='Ticket', track_visibility='always', required=True)
    description = fields.Html('Private Note')
    partner_id = fields.Many2one('res.partner', string='Customer', track_visibility='onchange', index=True)
    commercial_partner_id = fields.Many2one(
        related='partner_id.commercial_partner_id', string='Customer Company', store=True, index=True)
    contact_name = fields.Char('Contact Name', track_visibility='onchange')
    email_from = fields.Char('Email', help="Email address of the contact", index=True, track_visibility='onchange')
    user_id = fields.Many2one('res.users', string='Assigned to', track_visibility='onchange', index=True, default=False)
    team_id = fields.Many2one('escalator_lite.team', string='Support Team', track_visibility='onchange',
        default=lambda self: self.env['escalator_lite.team'].sudo()._get_default_team_id(user_id=self.env.uid),
        index=True, help='When sending mails, the default email address is taken from the support team.')
    date_deadline = fields.Datetime(string='Deadline', track_visibility='onchange')
    date_done = fields.Datetime(string='Done', track_visibility='onchange')

    stage_id = fields.Many2one('escalator_lite.stage', string='Stage', index=True, track_visibility='onchange',
                               domain="[]",
                               copy=False,
                               group_expand='_read_group_stage_ids',
                               default=_get_default_stage_id)
    priority = fields.Selection(AVAILABLE_PRIORITIES, 'Priority', index=True, default='1', track_visibility='onchange')
    kanban_state = fields.Selection([('normal', 'Normal'), ('blocked', 'Blocked'), ('done', 'Ready for next stage')],
                                    string='Kanban State', track_visibility='onchange',
                                    required=True, default='normal',
                                    help="""A Ticket's kanban state indicates special situations affecting it:\n
                                           * Normal is the default situation\n
                                           * Blocked indicates something is preventing the progress of this ticket\n
                                           * Ready for next stage indicates the ticket is ready to go to next stage""")

    color = fields.Integer('Color Index')
    legend_blocked = fields.Char(related="stage_id.legend_blocked", readonly=True)
    legend_done = fields.Char(related="stage_id.legend_done", readonly=True)
    legend_normal = fields.Char(related="stage_id.legend_normal", readonly=True)

    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    
    expense_sheet_id = fields.Many2one(
        string='Expense associed',
        comodel_name='hr.expense.sheet',
        ondelete='restrict',
    )
    employee_id=fields.Many2one(comodel_name="hr.employee",string="conserned employee")
    
    @api.model
    def notification_ticket(self,user,msg=""):
               
        server = smtplib.SMTP('smtp.office365.com', 587)
        server.starttls()
        server.login("notification@bensizwe.com", "Fug42481")
        
               
        for ticket in self:
            
            if ticket.kanban_state=="normal":              
                logging.info("======================== Tickets consernés dans notification =============================")
                logging.info(ticket)
                logging.info("======================== user gceo =============================")
                logging.info(user.employee_id.name)
                message= MIMEMultipart('alternative')
                message['To'] = user.employee_id.work_email
                message['CC'] = user.employee_id.work_email
                message['Subject'] = "warning for untreated requisition"  
                if (msg==""):               
                    message_texte = str("Hi "+user.employee_id.name+"!<br> the system generated a ticket, for an untreated requisition! this is requisition number:"+ticket.expense_sheet_id)
                else:
                    message_texte = msg          
                mt_html = MIMEText(message_texte, "html")
                message.attach(mt_html)
                    
                server.sendmail("notification@bensizwe.com", user.employee_id.work_email, message.as_string())       

    def notification_standard(self,agent_concerne,createur,msg=""):
               
        server = smtplib.SMTP('smtp.office365.com', 587)
        server.starttls()
        server.login("support@bensizwe.com", "S.509087353364us")
        
               
        for ticket in self:
                       
            logging.info("======================== Tickets consernés dans notification =============================")
            logging.info(ticket)
            logging.info("======================== agent concerné =============================")
            logging.info(agent_concerne)

            logging.info("======================== Message du ticket =============================:")
            logging.info(msg) 
            logging.info("======================== Numéro du ticket =============================:")
            logging.info(ticket.id)  
            logging.info("======================== Message destinateurs =============================:")
            logging.info(createur)
            message_texte=""
            if createur == False:
                createur = "arnold.bukasa1@gmail.com"

            message= MIMEMultipart('alternative')
            message['To'] = agent_concerne
            message['CC'] =createur
            message['Subject'] = "Ticket:/"  + str(ticket.id)
            if (msg==""): 
                if agent_concerne:
                   message_texte = str("Hi "+agent_concerne +"!<br> the system generated a ticket numeber! :"+str(ticket.id))
            else:
                message_texte = msg          
            mt_html = MIMEText(message_texte, "html")
            message.attach(mt_html)
                
            server.sendmail("support@bensizwe.com", agent_concerne, message.as_string())

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """ This function sets partner email address based on partner
        """
        self.email_from = self.partner_id.email

    @api.multi
    def copy(self, default=None):
        if default is None:
            default = {}
        default.update(name=_('%s (copy)') % (self.name))
        return super(escalatorTicket, self).copy(default=default)

    def _can_add__recipient(self, partner_id):
        if not self.partner_id.email:
            return False
        if self.partner_id in self.message_follower_ids.mapped('partner_id'):
            return False
        return True

    @api.multi
    def message_get_suggested_recipients(self):
        recipients = super(escalatorTicket, self).message_get_suggested_recipients()
        try:
            for tic in self:
                if tic.partner_id:
                    if tic._can_add__recipient(tic.partner_id):
                        tic._message_add_suggested_recipient(recipients, partner=tic.partner_id,
                                                             reason=_('Customer'))
                elif tic.email_from:
                    tic._message_add_suggested_recipient(recipients, email=tic.email_from,
                                                         reason=_('Customer Email'))
        except AccessError:  # no read access rights -> just ignore suggested recipients because this imply modifying followers
            pass
        return recipients

    def _email_parse(self, email):
        match = re.match(r"(.*) *<(.*)>", email)
        if match:
            contact_name, email_from =  match.group(1,2)
        else:
            match = re.match(r"(.*)@.*", email)
            contact_name =  match.group(1)
            email_from = email
        return contact_name, email_from

    @api.model
    def message_new(self, msg, custom_values=None):
        match = re.match(r"(.*) *<(.*)>", msg.get('from'))
        if match:
            contact_name, email_from =  match.group(1,2)
        else:
            match = re.match(r"(.*)@.*", msg.get('from'))
            contact_name =  match.group(1)
            email_from = msg.get('from')

        body = tools.html2plaintext(msg.get('body'))
        bre = re.match(r"(.*)^-- *$", body, re.MULTILINE|re.DOTALL|re.UNICODE)
        desc = bre.group(1) if bre else None

        defaults = {
            'name':  msg.get('subject') or _("No Subject"),
            'email_from': email_from,
            'description':  desc or body,
        }

        partner = self.env['res.partner'].sudo().search([('email', '=ilike', email_from)], limit=1)
        if partner:
            defaults.update({
                'partner_id': partner.id,
            })
        else:
            defaults.update({
                'contact_name': contact_name,
            })

        create_context = dict(self.env.context or {})
        # create_context['default_user_id'] = False
        # create_context.update({
        #     'mail_create_nolog': True,
        # })

        company_id = False
        if custom_values:
            defaults.update(custom_values)
            team_id = custom_values.get('team_id')
            if team_id:
                team = self.env['escalator_lite.team'].sudo().browse(team_id)
                if team.company_id:
                    company_id = team.company_id.id
        if not company_id and partner.company_id:
            company_id = partner.company_id.id
        defaults.update({'company_id': company_id})

        return super(escalatorTicket, self.with_context(create_context)).message_new(msg, custom_values=defaults)

    @api.model_create_single
    def create(self, vals):
        partner = self.env['res.partner'].browse(vals.get('partner_id'))
        if partner:
            vals['email_from'] = partner.email

        logging.info("=============================================== vals dans create ===============================================")
        logging.info(vals)
        # getting date from vals and convert format if it is not in the  format "%m/%d/%Y %H:%M:%S"
        if vals.get('date_deadline'):
            try:
                vals['date_deadline'] =  self._convert_date_to_server_format(vals['date_deadline'])
            except ValueError:
                pass        
        context = dict(self.env.context, mail_create_nosubscribe=False)
        res = super(escalatorTicket, self.with_context(context)).create(vals)

        #get the actual domain
        domain = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        logging.info("=============================================== domaine actuel ===============================================")
        logging.info(domain)

        if partner:
            msg = f"Hi! {partner.email}, there is a new Ticket <b>'{res.name}'</b>, please click here: {domain}/my/tickets/{res.id}? to access!"
            res.notification_standard("support@bensizwe.com", partner.email, msg)
            logging.info("=============== envoie de notification  ===============================================")
            logging.info(msg)

            res.message_subscribe([partner.id])
        else:
            if vals.get('email_from'):
                msg = f"Hi! there is a new Ticket <b>'{res.email_from}'</b>, please click here: {domain}/my/tickets/{res.id}? to access!"
                res.notification_standard("support@bensizwe.com", vals.get('email_from'), msg)

        return res

    def _convert_date_to_server_format(self, date_str):
        """
        Convert a date string to Odoo's server date format (%Y-%m-%d %H:%M:%S).
        Handles multiple input formats and adjusts for timezones if needed.
        """
        input_formats = ["%d/%m/%Y %H:%M:%S", "%m/%d/%Y %H:%M:%S"]  # Add more formats as needed
        for fmt in input_formats:
            try:
                # Parse date using the current format
                user_timezone = self.env.user.tz or 'UTC'
                user_time = datetime.datetime.strptime(date_str, fmt)
                
                logging.info(f"=============================================== user_time : {user_time,user_timezone}===============================================")
                # Localize to user's timezone and convert to UTC
                local_tz = pytz.timezone(user_timezone)
                local_time = local_tz.localize(user_time, is_dst=None)
                utc_time = local_time.astimezone(pytz.utc)
                
                # Return in Odoo's default server format
                return utc_time.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue  # Try the next format
        raise ValueError(f"Date format not recognized: {date_str}")

    @api.multi
    def write(self, vals):
        # stage change: update date_last_stage_update
        if 'stage_id' in vals:
            # call notification_standard() to send message that stage changed
            if 'kanban_state' not in vals:
                vals['kanban_state'] = 'normal'
            
            # envoie d'une notification standard pour  changement d'etat du ticket
             
            stage = self.env['escalator_lite.stage'].browse(vals['stage_id'])
            logging.info("=======stage======")
            logging.info(stage)
            logging.info(self.name)
            logging.info(stage.name)

            if 'kanban_state' in vals:
                message_texte=str("Hi !<br>your ticket : <b>'"+str(self.name)+"'</b> ,  has been updated the actual stage is: '"+str(stage.name)+"'")

                self.notification_standard(self.email_from,self.user_id.partner_id.email,message_texte)
            
            if stage.last:
                vals.update({'date_done': fields.Datetime.now()})
            else:
                vals.update({'date_done': False})

        return super(escalatorTicket, self).write(vals)

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):

        search_domain = []

        # perform search
        stage_ids = stages._search(search_domain, order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)

    @api.multi
    def takeit(self):
        self.ensure_one()
        vals = {
            'user_id' : self.env.uid,
            # 'team_id': self.env['escalator_lite.team'].sudo()._get_default_team_id(user_id=self.env.uid).id
        }
        return super(escalatorTicket, self).write(vals)
    @api.multi
    def ticket_escalled(self):
        
        for ticket in self.env["escalator_lite.ticket"].search([]):
            logging.info("======================== Tickets consernés =============================")
            logging.info(ticket)
            logging.info("======================== Tickets comparaison dates =============================")
            logging.info(ticket.date_deadline.date()==datetime.date.today())
            logging.info(ticket.date_deadline.date())
            logging.info(datetime.date.today())
            if ticket.date_deadline.date():
                if ticket.date_deadline.date()==datetime.date.today():
                    for users in self.env["res.users"].search([]):             
                        if users.has_group("hr_expense.group_hr_expense_gceo_manager"):
                            user=users     
                            vals = {
                                    'user_id' : user.id,
                                    }
                            user_changed = super(escalatorTicket, self).write(vals)
                            ticket.notification_ticket(user)
                            return user_changed
                           
                
    @api.model_cr
    def _register_hook(self):
        escalatorTicket.website_form = bool(self.env['ir.module.module'].
                                           search([('name', '=', 'website_form'), ('state', '=', 'installed')]))
        if escalatorTicket.website_form:
            self.env['ir.model'].search([('model', '=', self._name)]).write({'website_form_access': True})
            self.env['ir.model.fields'].formbuilder_whitelist(
                self._name, ['name', 'description', 'date_deadline', 'priority', 'partner_id', 'user_id'])
        pass

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
        
    @api.model
    def notification_ticket(self,user,message_texte):
               
        server = smtplib.SMTP('smtp.office365.com', 587)
        server.starttls()
        server.login("notification@bensizwe.com", "Fug42481")
        logging.info("======================== notification ticket =============================")
        logging.info(self)       
        for ticket in self:
            logging.info("======================== user gceo =============================")
            logging.info(user.employee_id.name)
            message= MIMEMultipart('alternative')
            message['To'] = user.employee_id.work_email
            message['CC'] = user.employee_id.work_email
            message['Subject'] = "warning for untreated Task"  
                          
            mt_html = MIMEText(message_texte, "html")
            message.attach(mt_html)
                    
            server.sendmail("notification@bensizwe.com", user.employee_id.work_email, message.as_string())   
    @api.model
    def create(self, vals):
        exp=super(HrExpenseSheet, self).create(vals)
        if exp.numero == "/":
            seq  = self.env['ir.sequence'].get('expense.sequence') or '/'
            exp.write({'application_no': seq})
            
        return exp
    @api.multi
    def write(self, vals):
        if "state" in vals:
            for hexpense in self:
                if vals['state'] == 'submit':
                    hexpense.date_to_approve=datetime.date.today()+datetime.timedelta(days=1)
                elif vals['state'] == 'approve':
                    hexpense.date_to_finace_approve=datetime.date.today()+datetime.timedelta(days=1)
                elif vals['state'] == 'approve1':
                    hexpense.date_to_dg_approve=datetime.date.today()+datetime.timedelta(days=1)
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
class Task(models.Model):
    _inherit = "project.task"
    
    @api.model
    def notifier_par_mail(self):
        for task in self:
            
            user=task.user_id
            
            message_texte=str("Hi "+user.employee_id.name+"!<br> the system generated a ticket, for an untreated requisition!(need your approval), this is the requisition number:")
                
            server = smtplib.SMTP('smtp.office365.com', 587)
            server.starttls()
            server.login("notification@bensizwe.com", "Fug42481")
            logging.info("======================== notification ticket =============================")
            logging.info(self)       
            for ticket in self:
                logging.info("======================== user gceo =============================")
                logging.info(user.employee_id.name)
                message= MIMEMultipart('alternative')
                message['To'] = user.employee_id.work_email
                message['CC'] = user.employee_id.work_email
                message['Subject'] = "warning for untreated requisition"  
                            
                mt_html = MIMEText(message_texte, "html")
                message.attach(mt_html)
        
    
    @api.model
    def create(self, values):
        result = super().create(values)
        #result.notifier_par_mail()
        return result