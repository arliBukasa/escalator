# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.tools import safe_eval


class EscalatorTeam(models.Model):
    _name = "escalator.team"
    _inherit = ['mail.thread', 'mail.alias.mixin']
    _description = "Escalator Team"
    _order = "name"
    _rec_names_search = ['name', 'alias_name']  # Add this for better search

    name = fields.Char('Team Name', required=True, translate=True, tracking=True)
    user_id = fields.Many2one('res.users', string='Team Leader', tracking=True)
    member_ids = fields.Many2many(
        'res.users', 'escalator_team_users_rel', 'team_id', 'user_id',
        string='Team Members',
        help="Users who are members of this team.")
    
    # Email configuration
    email = fields.Char('Email', related='alias_id.email', readonly=False)
    alias_id = fields.Many2one(
        'mail.alias', string='Alias', ondelete='restrict', required=True,
        help="The email address associated with this team. New emails will automatically create new tickets assigned to the team.")
    
    # Visual options
    color = fields.Integer('Color Index', default=0)
    active = fields.Boolean(
        default=True,
        help="If the active field is set to false, it will allow you to hide the team without removing it.")
    
    # Company
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company,
        help="Company related to this team.")

    @api.model
    def create(self, vals):
        # Create team and alias
        team = super(EscalatorTeam, self.with_context(mail_create_nosubscribe=True)).create(vals)
        
        # Update alias settings
        if not team.alias_id and not vals.get('alias_name'):
            alias_vals = team._alias_get_creation_values()
            alias = self.env['mail.alias'].create(alias_vals)
            team.alias_id = alias.id
            
        return team

    def write(self, vals):
        # Handle alias updates
        if 'alias_name' in vals or 'alias_defaults' in vals:
            alias_vals = self._alias_get_creation_values()
            self.alias_id.write(alias_vals)
            
        return super(EscalatorTeam, self).write(vals)

    def _alias_get_creation_values(self):
        """Return values to create an alias for this team."""
        self.ensure_one()
        alias_name = self.alias_name or self.name
        return {
            'alias_name': alias_name,
            'alias_model_id': self.env['ir.model']._get('escalator.ticket').id,
            'alias_contact': 'partners',
            'alias_parent_thread_id': self.id,
            'alias_defaults': {'team_id': self.id},
        }

    @api.model
    @api.returns('self', lambda value: value.id if value else False)
    def _get_default_team_id(self, user_id=None):
        """ Get the default team for the current user.
        
        :param int user_id: Optional user ID (default: current user)
        :return: team ID or False if no team found
        """
        if not user_id:
            user_id = self.env.uid
            
        # Check context for default team
        if 'default_team_id' in self.env.context:
            return self.env.context.get('default_team_id')
            
        # Try to find a team where user is member or team leader
        team = self.sudo().search([
            '|', 
            ('user_id', '=', user_id), 
            ('member_ids', 'in', [user_id])
        ], limit=1)
        
        # Fallback to any active team
        if not team:
            team = self.sudo().search([('active', '=', True)], limit=1)
            
        return team.id if team else False
        defaults['team_id'] = self.id
        values['alias_defaults'] = defaults
        return values
