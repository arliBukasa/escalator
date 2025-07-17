# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class TicketCategory(models.Model):
    """Model for ticket categories to better organize and classify tickets"""
    _name = "escalator_lite.category"
    _description = "Ticket Category"
    _rec_name = 'name'
    _order = "sequence, name, id"

    name = fields.Char('Category Name', required=True, translate=True)
    sequence = fields.Integer('Sequence', default=10, help="Used to order categories.")
    description = fields.Text('Description', help="Detailed description of this category.")
    color = fields.Integer('Color Index', default=0)
    active = fields.Boolean('Active', default=True)
    parent_id = fields.Many2one('escalator_lite.category', string='Parent Category', index=True, ondelete='cascade')
    child_ids = fields.One2many('escalator_lite.category', 'parent_id', string='Child Categories')
    ticket_count = fields.Integer('Ticket Count', compute='_compute_ticket_count')
    
    @api.depends('name')
    def _compute_ticket_count(self):
        for category in self:
            category.ticket_count = self.env['escalator_lite.ticket'].search_count([
                ('category_id', '=', category.id)
            ])
    
    @api.constrains('parent_id')
    def _check_category_recursion(self):
        if not self._check_recursion():
            raise ValidationError(_('You cannot create recursive categories.'))
    
    def name_get(self):
        result = []
        for category in self:
            name = category.name
            if category.parent_id:
                name = f"{category.parent_id.name} / {name}"
            result.append((category.id, name))
        return result
    
    def action_view_tickets(self):
        """Action to view tickets in this category"""
        action = self.env.ref('escalator.action_escalator_ticket').read()[0]
        action['domain'] = [('category_id', '=', self.id)]
        action['context'] = {'default_category_id': self.id}
        return action
