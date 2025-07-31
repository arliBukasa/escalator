# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import timedelta


class TicketSLA(models.Model):
    """Model for Service Level Agreements to manage response and resolution times"""
    _name = "escalator_lite.sla"
    _description = "Service Level Agreement"
    _rec_name = 'name'
    _order = "priority desc, sequence, name"

    name = fields.Char('SLA Name', required=True, translate=True)
    sequence = fields.Integer('Sequence', default=10)
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Urgent'),
    ], string='Priority Level', required=True, default='1')
    
    category_ids = fields.Many2many('escalator_lite.category', string='Categories')
    team_ids = fields.Many2many('escalator_lite.team', string='Teams')
    
    # Response time (time to first response)
    response_time = fields.Float('Response Time (Hours)', required=True, default=24.0)
    response_stage_id = fields.Many2one('escalator_lite.stage', string='Response Stage', 
                                       help="Stage that indicates response has been made")
    
    # Resolution time (time to close ticket)
    resolution_time = fields.Float('Resolution Time (Hours)', required=True, default=72.0)
    
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    
    escalation_enabled = fields.Boolean('Enable Escalation', default=True)
    escalation_time_before_deadline = fields.Float('Escalation Time Before Deadline (Hours)', 
                                                   default=2.0, help="Hours before deadline to escalate")
    escalation_user_ids = fields.Many2many('res.users', string='Escalation Users')
    
    @api.model
    def get_sla_for_ticket(self, ticket):
        """Get the appropriate SLA for a ticket"""
        domain = [('active', '=', True)]
        
        # Filter by priority
        if ticket.priority:
            domain.append(('priority', '=', ticket.priority))
        
        # Filter by category
        if ticket.category_id:
            domain.append('|')
            domain.append(('category_ids', '=', False))
            domain.append(('category_ids', 'in', ticket.category_id.id))
        
        # Filter by team
        if ticket.team_id:
            domain.append('|')
            domain.append(('team_ids', '=', False))
            domain.append(('team_ids', 'in', ticket.team_id.id))
        
        sla = self.search(domain, limit=1)
        return sla
    
    def check_sla_violations(self):
        """Check for SLA violations and take action"""
        tickets = self.env['escalator_lite.ticket'].search([
            ('is_final_stage', '=', False),  # Open tickets only
            ('active', '=', True)
        ])
        
        for ticket in tickets:
            sla = self.get_sla_for_ticket(ticket)
            if sla:
                # Check response time violation
                if ticket.create_date:
                    response_deadline = ticket.create_date + timedelta(hours=sla.response_time)
                    if fields.Datetime.now() > response_deadline and not ticket.date_first_response:
                        ticket._sla_response_violation(sla)
                
                # Check resolution time violation
                if ticket.date_deadline:
                    if fields.Datetime.now() > ticket.date_deadline:
                        ticket._sla_resolution_violation(sla)
                
                # Check escalation
                if sla.escalation_enabled and ticket.date_deadline:
                    escalation_time = ticket.date_deadline - timedelta(hours=sla.escalation_time_before_deadline)
                    if fields.Datetime.now() > escalation_time and not ticket.is_escalated:
                        ticket.escalate_ticket()


class TicketInheritSLA(models.Model):
    _inherit = 'escalator_lite.ticket'
    
    sla_id = fields.Many2one('escalator_lite.sla', string='SLA', compute='_compute_sla', store=True)
    date_first_response = fields.Datetime('First Response Date', readonly=True)
    sla_response_status = fields.Selection([
        ('met', 'Met'),
        ('violated', 'Violated'),
        ('pending', 'Pending')
    ], string='Response SLA Status', default='pending', readonly=True)
    sla_resolution_status = fields.Selection([
        ('met', 'Met'),
        ('violated', 'Violated'),
        ('pending', 'Pending')
    ], string='Resolution SLA Status', default='pending', readonly=True)
    
    @api.depends('priority', 'category_id', 'team_id')
    def _compute_sla(self):
        for ticket in self:
            ticket.sla_id = self.env['escalator_lite.sla'].get_sla_for_ticket(ticket)
            # Set deadline based on SLA
            if ticket.sla_id and ticket.create_date and not ticket.date_deadline:
                deadline = ticket.create_date + timedelta(hours=ticket.sla_id.resolution_time)
                ticket.date_deadline = deadline
    
    def _sla_response_violation(self, sla):
        """Handle SLA response violation"""
        self.sla_response_status = 'violated'
        # Send notification
        subject = f"SLA Response Violation: {self.name}"
        body = f"Ticket {self.name} has violated the response SLA of {sla.response_time} hours."
        self.message_post(subject=subject, body=body, subtype='mail.mt_comment')
    
    def _sla_resolution_violation(self, sla):
        """Handle SLA resolution violation"""
        self.sla_resolution_status = 'violated'
        # Send notification
        subject = f"SLA Resolution Violation: {self.name}"
        body = f"Ticket {self.name} has violated the resolution SLA of {sla.resolution_time} hours."
        self.message_post(subject=subject, body=body, subtype='mail.mt_comment')
    
    def write(self, vals):
        # Track first response
        if 'stage_id' in vals and not self.date_first_response:
            sla = self.env['escalator_lite.sla'].get_sla_for_ticket(self)
            if sla and sla.response_stage_id:
                new_stage = self.env['escalator_lite.stage'].browse(vals['stage_id'])
                if new_stage.id == sla.response_stage_id.id:
                    vals['date_first_response'] = fields.Datetime.now()
                    vals['sla_response_status'] = 'met'
        
        # Track resolution
        if vals.get('date_done'):
            vals['sla_resolution_status'] = 'met'
        
        return super(TicketInheritSLA, self).write(vals)
