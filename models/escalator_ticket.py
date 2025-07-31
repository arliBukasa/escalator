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


class EscalatorTicket(models.Model):
    _name = "escalator.ticket"
    _description = "Escalator Ticket"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin', 'utm.mixin']
    _order = "priority desc, create_date desc"
    _mail_post_access = 'read'

    @api.model
    def _get_default_stage_id(self):
        return self.env['escalator_lite.stage'].search([], order='sequence', limit=1)

    name = fields.Char(string='Ticket', tracking=True, required=True)
    description = fields.Html('Private Note', sanitize=True)
    partner_id = fields.Many2one('res.partner', string='Customer', tracking=True, index=True)
    commercial_partner_id = fields.Many2one(
        related='partner_id.commercial_partner_id', string='Customer Company', store=True, index=True)
    contact_name = fields.Char('Contact Name', tracking=True)
    email_from = fields.Char('Email', help="Email address of the contact", index=True, tracking=True)
    user_id = fields.Many2one('res.users', string='Assigned to', tracking=True, index=True, default=False)
    team_id = fields.Many2one('escalator.team', string='Support Team', tracking=True,
        default=lambda self: self.env['escalator.team'].sudo()._get_default_team_id(user_id=self.env.uid),
        index=True, help='When sending mails, the default email address is taken from the support team.')
    date_deadline = fields.Datetime(string='Deadline', tracking=True)
    date_done = fields.Datetime(string='Done', tracking=True)

    stage_id = fields.Many2one('escalator.stage', string='Stage', index=True, tracking=True,
                             domain="[]",
                             copy=False,
                             group_expand='_read_group_stage_ids',
                             default=_get_default_stage_id)
    priority = fields.Selection(AVAILABLE_PRIORITIES, string='Priority', index=True, default='1', tracking=True)
    kanban_state = fields.Selection([('normal', 'In Progress'), 
                                   ('blocked', 'Blocked'), 
                                   ('done', 'Ready for next stage')],
                                    string='Kanban State', 
                                    tracking=True,
                                    required=True, 
                                    default='normal',
                                    help="""A Ticket's kanban state indicates special situations affecting it:
                                     * Normal is the default situation
                                     * Blocked indicates something is preventing the progress of this ticket
                                     * Ready for next stage indicates the ticket is ready to be pulled to the next stage""")
    color = fields.Integer('Color Index', default=0)
    legend_blocked = fields.Char(related="stage_id.legend_blocked", readonly=True)
    legend_done = fields.Char(related="stage_id.legend_done", readonly=True)
    legend_normal = fields.Char(related="stage_id.legend_normal", readonly=True)

    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company',
                                default=lambda self: self.env.company)
    
    # Tracking fields
    create_date = fields.Datetime('Creation Date', readonly=True, index=True)
    write_date = fields.Datetime('Last Updated', readonly=True, index=True)
    create_uid = fields.Many2one('res.users', string='Created by', readonly=True)
    write_uid = fields.Many2one('res.users', string='Last Updated by', readonly=True)

    expense_sheet_id = fields.Many2one(
        string='Expense associed',
        comodel_name='hr.expense.sheet',
        ondelete='restrict',
    )
    employee_id = fields.Many2one(comodel_name="hr.employee", string="Concerned employee")
    progress = fields.Float(string='Progress (%)', compute='_compute_progress', store=True)
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    category_id = fields.Many2one('escalator_lite.category', string='Category')
    estimated_hours = fields.Float(string='Estimated Hours')
    actual_hours = fields.Float(string='Actual Hours')
    resolution = fields.Text(string='Resolution')
    is_escalated = fields.Boolean(string='Is Escalated', default=False)
    escalation_date = fields.Datetime(string='Escalation Date')
    
    resolution_time = fields.Float(string='Resolution Time (Hours)', compute='_compute_resolution_time', store=True)
    is_final_stage = fields.Boolean(string='Is Final Stage', compute='_compute_is_final_stage', store=True)
    
    @api.depends('stage_id')
    def _compute_progress(self):
        for ticket in self:
            if ticket.stage_id:
                # Calculate progress based on stage sequence
                all_stages = self.env['escalator_lite.stage'].search([], order='sequence')
                if all_stages:
                    current_position = 0
                    for i, stage in enumerate(all_stages):
                        if stage.id == ticket.stage_id.id:
                            current_position = i + 1
                            break
                    ticket.progress = (current_position / len(all_stages)) * 100
                else:
                    ticket.progress = 0
            else:
                ticket.progress = 0
    
    @api.depends('create_date', 'date_done')
    def _compute_resolution_time(self):
        for ticket in self:
            if ticket.create_date and ticket.date_done:
                delta = ticket.date_done - ticket.create_date
                ticket.resolution_time = delta.total_seconds() / 3600  # in hours
            else:
                ticket.resolution_time = 0
    
    @api.depends('stage_id.last')
    def _compute_is_final_stage(self):
        for ticket in self:
            ticket.is_final_stage = ticket.stage_id.last if ticket.stage_id else False
    
    def escalate_ticket(self):
        """Escalate ticket to manager or next level"""
        for ticket in self:
            if not ticket.is_escalated:
                # Find manager or escalation user
                escalation_users = self.env['res.users'].search([
                    ('groups_id', 'in', self.env.ref('base.group_system').id)
                ])
                if escalation_users:
                    ticket.write({
                        'user_id': escalation_users[0].id,
                        'is_escalated': True,
                        'escalation_date': fields.Datetime.now(),
                        'priority': '3',  # Set to urgent
                    })
                    # Send notification
                    msg = f"Ticket '{ticket.name}' has been escalated and assigned to you."
                    ticket.notification_standard(escalation_users[0].email, ticket.email_from, msg)
    
    @api.model
    def auto_escalate_overdue_tickets(self):
        """Cron job to auto-escalate overdue tickets"""
        overdue_tickets = self.search([
            ('date_deadline', '<', fields.Datetime.now()),
            ('is_final_stage', '=', False),
            ('is_escalated', '=', False)
        ])
        for ticket in overdue_tickets:
            ticket.escalate_ticket()
    
    @api.model
    def notification_ticket(self, user, msg=""):
        """Send notification email using Odoo's mail system instead of direct SMTP"""
        try:
            # Use Odoo's mail system instead of direct SMTP
            mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
            if not mail_server:
                logging.warning("No mail server configured in Odoo")

                return False
                
            for ticket in self:
                if ticket.kanban_state == "normal":              
                    logging.info("======================== Tickets consernés dans notification =============================")
                    logging.info(ticket)
                    logging.info("======================== user gceo =============================")
                    logging.info(user.employee_id.name)
                    
                    subject = "Warning for untreated requisition"
                    if msg == "":               
                        body_html = f"Hi {user.employee_id.name}!<br> The system generated a ticket for an untreated requisition! This is requisition number: {ticket.expense_sheet_id or 'N/A'}"
                    else:
                        body_html = msg
                    
                    # Create mail using Odoo's mail system
                    mail_values = {
                        'subject': subject,
                        'body_html': body_html,
                        'email_to': user.employee_id.work_email,
                        'email_from': mail_server.smtp_user or 'noreply@company.com',
                    }
                    
                    mail = self.env['mail.mail'].sudo().create(mail_values)
                    try:
                        #mail.send()
                        logging.info(f"Email sent successfully to {user.employee_id.work_email}")
                    except Exception as e:
                        logging.error(f"Failed to send email: {str(e)}")
                        
        except Exception as e:
            logging.error(f"Error in notification_ticket: {str(e)}")
            return False
        
        return True       

    def notification_standard(self, agent_concerne, createur, msg=""):
        """Send notification email using direct SMTP with improved From header"""
        try:
            server = smtplib.SMTP('smtp.office365.com', 587)
            server.starttls()
            server.login("support@bensizwe.com", "H&890601727549ow")
            
            for ticket in self:
                logging.info("======================== Tickets concernés dans notification =============================")
                logging.info(ticket)
                logging.info("======================== agent concerné =============================")
                logging.info(agent_concerne)
                logging.info("======================== Message du ticket =============================:")
                logging.info(msg) 
                logging.info("======================== Numéro du ticket =============================:")
                logging.info(ticket.id)  
                logging.info("======================== Message destinateurs =============================:")
                logging.info(createur)
                
                message_texte = ""
                if createur == False:
                    createur = "arnold.bukasa1@gmail.com"

                message = MIMEMultipart('alternative')
                message['From'] = "support@bensizwe.com"  # IMPORTANT: Ajouter From
                message['To'] = agent_concerne
                message['CC'] = createur
                message['Subject'] = "Ticket:/" + str(ticket.id)
                
                if msg == "": 
                    if agent_concerne:
                       message_texte = str("Hi " + agent_concerne + "!<br> the system generated a ticket number: " + str(ticket.id))
                else:
                    message_texte = msg          
                    
                mt_html = MIMEText(message_texte, "html")
                message.attach(mt_html)
                
                try:
                    server.sendmail("support@bensizwe.com", agent_concerne, message.as_string())
                    logging.info(f"Email sent successfully to {agent_concerne}")
                except Exception as e:
                    logging.error(f"Failed to send email to {agent_concerne}: {str(e)}")
            
            server.quit()
            logging.info("======================== Email envoyé avec succès =============================")
            
        except Exception as e:
            logging.error(f"Error in notification_standard: {str(e)}")
            return False
        
        return True

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """ This function sets partner email address based on partner
        """
        self.email_from = self.partner_id.email

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
            contact_name, email_from = match.group(1, 2)
        else:
            match = re.match(r"(.*)@.*", email)
            if match:
                contact_name = match.group(1)
            else:
                contact_name = email
            email_from = email
        return contact_name, email_from

    @api.model
    def message_new(self, msg, custom_values=None):
        match = re.match(r"(.*) *<(.*)>", msg.get('from'))
        if match:
            contact_name, email_from = match.group(1, 2)
        else:
            match = re.match(r"(.*)@.*", msg.get('from'))
            if match:
                contact_name = match.group(1)
            else:
                contact_name = msg.get('from', 'Unknown')
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

    @api.model_create_multi
    def create(self, vals_list):
        if not isinstance(vals_list, list):
            vals_list = [vals_list]
        
        tickets = []
        for vals in vals_list:
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
            res = super(escalatorTicket, self.with_context(context)).create([vals])
            tickets.append(res)

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
        
        return tickets[0] if len(tickets) == 1 else tickets

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

    def write(self, vals):
        # Capturer l'ancien assigné avant modification
        old_user_id = self.user_id.id if self.user_id else False
        
        # stage change: update date_last_stage_update
        if 'stage_id' in vals:
            # call notification_standard() to send message that stage changed
            if 'kanban_state' not in vals:
                vals['kanban_state'] = 'normal'
            
            # envoie d'une notification standard pour changement d'etat du ticket
            stage = self.env['escalator_lite.stage'].browse(vals['stage_id'])
            logging.info("=======stage======")
            logging.info(stage)
            logging.info(self.name)
            logging.info(stage.name)

            if 'kanban_state' in vals:
                message_texte = str("Hi !<br>your ticket : <b>'" + str(self.name) + "'</b> ,  has been updated the actual stage is: '" + str(stage.name) + "'")
                self.notification_standard(self.email_from, self.user_id.partner_id.email if self.user_id else "support@bensizwe.com", message_texte)
            
            if stage.last:
                vals.update({'date_done': fields.Datetime.now()})
            else:
                vals.update({'date_done': False})

        # User assignment change: send notifications
        if 'user_id' in vals:
            new_user_id = vals['user_id']
            
            # Si l'assignation change vraiment
            if old_user_id != new_user_id:
                result = super(escalatorTicket, self).write(vals)
                
                # Récupérer les utilisateurs
                old_user = self.env['res.users'].browse(old_user_id) if old_user_id else None
                new_user = self.env['res.users'].browse(new_user_id) if new_user_id else None
                
                # Notification au nouvel assigné
                if new_user and new_user.email:
                    message_new = f"Hi {new_user.name}!<br>You have been assigned the ticket <b>'{self.name}'</b> (#{self.id}).<br>Priority: {dict(AVAILABLE_PRIORITIES).get(self.priority, 'Normal')}<br>Deadline: {self.date_deadline or 'Not set'}"
                    self.notification_standard(new_user.email, self.email_from or "support@bensizwe.com", message_new)
                
                # Notification au client/rapporteur
                if self.email_from:
                    domain = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                    if new_user:
                        message_customer = f"Hi!<br>Your ticket <b>'{self.name}'</b> (#{self.id}) has been assigned to {new_user.name}.<br>You can track its progress here: {domain}/my/tickets/{self.id}"
                    else:
                        message_customer = f"Hi!<br>Your ticket <b>'{self.name}'</b> (#{self.id}) has been unassigned.<br>You can track its progress here: {domain}/my/tickets/{self.id}"
                    self.notification_standard(self.email_from, new_user.email if new_user else "support@bensizwe.com", message_customer)
                
                # Notification à l'ancien assigné s'il y en avait un
                if old_user and old_user.email:
                    if new_user:
                        message_old = f"Hi {old_user.name}!<br>The ticket <b>'{self.name}'</b> (#{self.id}) has been reassigned from you to {new_user.name}."
                    else:
                        message_old = f"Hi {old_user.name}!<br>The ticket <b>'{self.name}'</b> (#{self.id}) has been unassigned from you."
                    self.notification_standard(old_user.email, new_user.email if new_user else "support@bensizwe.com", message_old)
                
                return result
            else:
                return super(escalatorTicket, self).write(vals)
        else:
            return super(escalatorTicket, self).write(vals)

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):

        search_domain = []

        # perform search
        stage_ids = stages._search(search_domain, order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)

    def takeit(self):
        """Assign ticket to current user and send notification"""
        self.ensure_one()
        old_user = self.user_id
        
        vals = {
            'user_id': self.env.uid,
            # 'team_id': self.env['escalator_lite.team'].sudo()._get_default_team_id(user_id=self.env.uid).id
        }
        
        result = super(escalatorTicket, self).write(vals)
        
        # Send notification if user changed
        if old_user.id != self.env.uid:
            current_user = self.env.user
            
            # Notification to the new assignee (current user)
            if current_user.email:
                message_self = f"Hi {current_user.name}!<br>You have taken the ticket <b>'{self.name}'</b> (#{self.id}).<br>Priority: {dict(AVAILABLE_PRIORITIES).get(self.priority, 'Normal')}<br>Deadline: {self.date_deadline or 'Not set'}"
                self.notification_standard(current_user.email, self.email_from or "support@bensizwe.com", message_self)
            
            # Notification to the customer/reporter
            if self.email_from:
                domain = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                message_customer = f"Hi!<br>Your ticket <b>'{self.name}'</b> (#{self.id}) has been assigned to {current_user.name}.<br>You can track its progress here: {domain}/my/tickets/{self.id}"
                self.notification_standard(self.email_from, current_user.email, message_customer)
            
            # Notification to the previous assignee if there was one
            if old_user and old_user.email and old_user.id != self.env.uid:
                message_old = f"Hi {old_user.name}!<br>The ticket <b>'{self.name}'</b> (#{self.id}) has been reassigned from you to {current_user.name}."
                self.notification_standard(old_user.email, current_user.email, message_old)
        
        return result
    
    def assign_to_me(self):
        """Alternative method to assign ticket to current user"""
        return self.takeit()
    
    def assign_to_user(self, user_id):
        """Assign ticket to specific user with notifications"""
        self.ensure_one()
        old_user = self.user_id
        new_user = self.env['res.users'].browse(user_id)
        
        if not new_user:
            return False
        
        vals = {'user_id': user_id}
        result = super(escalatorTicket, self).write(vals)
        
        # Send notifications
        if old_user.id != user_id:
            # Notification to the new assignee
            if new_user.email:
                message_new = f"Hi {new_user.name}!<br>You have been assigned the ticket <b>'{self.name}'</b> (#{self.id}).<br>Priority: {dict(AVAILABLE_PRIORITIES).get(self.priority, 'Normal')}<br>Deadline: {self.date_deadline or 'Not set'}"
                self.notification_standard(new_user.email, self.email_from or "support@bensizwe.com", message_new)
            
            # Notification to the customer/reporter
            if self.email_from:
                domain = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                message_customer = f"Hi!<br>Your ticket <b>'{self.name}'</b> (#{self.id}) has been assigned to {new_user.name}.<br>You can track its progress here: {domain}/my/tickets/{self.id}"
                self.notification_standard(self.email_from, new_user.email, message_customer)
            
            # Notification to the previous assignee if there was one
            if old_user and old_user.email:
                message_old = f"Hi {old_user.name}!<br>The ticket <b>'{self.name}'</b> (#{self.id}) has been reassigned from you to {new_user.name}."
                self.notification_standard(old_user.email, new_user.email, message_old)
        
        return result
    def ticket_escalled(self):
        
        for ticket in self.env["escalator_lite.ticket"].search([]):
            logging.info("======================== Tickets consernés =============================")
            logging.info(ticket)
            logging.info("======================== Tickets comparaison dates =============================")
            logging.info(ticket.date_deadline.date()==datetime.date.today())
            logging.info(ticket.date_deadline.date())
            logging.info(datetime.date.today())
            if ticket.date_deadline.date():
                if ticket.date_deadline.date() == datetime.date.today():
                    for users in self.env["res.users"].search([]):
                        if users.has_group("base.group_system"):
                            user = users
                            vals = {
                                'user_id': user.id,
                            }
                            user_changed = super().write(vals)
                            ticket.notification_ticket(user)
                            return user_changed
                
    @api.model
    def _register_hook(self):
        # Simplified hook registration for website forms
        try:
            self.env['ir.module.module'].search([('name', '=', 'website_form'), ('state', '=', 'installed')])
            escalatorTicket.website_form = True
        except Exception:
            escalatorTicket.website_form = False
        pass

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