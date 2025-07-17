# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import OrderedDict
import json

from odoo import http, _
from odoo.addons.portal.controllers.portal import CustomerPortal as BaseCustomerPortal
from odoo.http import request
from odoo.osv.expression import OR


class CustomerPortal(BaseCustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        # domain is needed to hide non portal project for employee
        # portal users can't see the privacy_visibility, fetch the domain for them in sudo
        ticket_count = request.env['escalator_lite.ticket'].search_count([])
        values.update({
            'ticket_count': ticket_count,
        })
        return values

    @http.route(['/my/tickets', '/my/tickets/page/<int:page>'], type='http', auth="user", website=True)
    def my_tickets(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, search=None, search_in='content', **kw):
        groupby = 'none'  # kw.get('groupby', 'project') #TODO master fix this
        values = self._prepare_portal_layout_values()

        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc'},
            'name': {'label': _('Title'), 'order': 'name'},
            'stage': {'label': _('Stage'), 'order': 'stage_id'},
#            'update': {'label': _('Last Stage Update'), 'order': 'date_last_stage_update desc'},
        }
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'open': {'label': _('In Progress'), 'domain': [('is_final_stage', '=', False)]},
            'closed': {'label': _('Closed'), 'domain': [('is_final_stage', '=', True)]},
            'urgent': {'label': _('Urgent'), 'domain': [('priority', '=', '3')]},
            'high': {'label': _('High Priority'), 'domain': [('priority', '=', '2')]},
            'my': {'label': _('Assigned to me'), 'domain': [('user_id', '=', request.env.user.id)]},
        }
        searchbar_inputs = {
            'content': {'input': 'content', 'label': _('Search <span class="nolabel"> (in Content)</span>')},
            'message': {'input': 'message', 'label': _('Search in Messages')},
            'customer': {'input': 'customer', 'label': _('Search in Customer')},
            'stage': {'input': 'stage', 'label': _('Search in Stages')},
            'all': {'input': 'all', 'label': _('Search in All')},
        }
        searchbar_groupby = {
            'none': {'input': 'none', 'label': _('None')},
            'stage': {'input': 'stage', 'label': _('Stage')},
            'priority': {'input': 'priority', 'label': _('Priority')},
            'user': {'input': 'user', 'label': _('Assigned User')},
        }

        domain = ([])

        # default sort by value
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        # default filter by value
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']

        # archive groups - Default Group By 'create_date'
        archive_groups = self._get_archive_groups('escalator_lite.ticket', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # search
        if search and search_in:
            search_domain = []
            if search_in in ('content', 'all'):
                search_domain = OR([search_domain, ['|', ('name', 'ilike', search), ('description', 'ilike', search)]])
            if search_in in ('customer', 'all'):
                search_domain = OR([search_domain, [('partner_id', 'ilike', search)]])
            if search_in in ('message', 'all'):
                search_domain = OR([search_domain, [('message_ids.body', 'ilike', search)]])
            if search_in in ('stage', 'all'):
                search_domain = OR([search_domain, [('stage_id', 'ilike', search)]])
            domain += search_domain

        ticket_count = request.env['escalator_lite.ticket'].search_count(domain)
        # pager
        pager = request.website.pager(
            url="/my/tickets",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby, 'search_in': search_in, 'search': search},
            # url_args={'date_begin': date_begin, 'date_end': date_end},
            total=ticket_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        escalator_ticket = request.env['escalator_lite.ticket'].search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])

        values.update({
            'date_begin': date_begin,
            'date_end': date_end,
            'tickets': escalator_ticket,
            'page_name': 'ticket',
            'archive_groups': archive_groups,
            'default_url': '/my/tickets',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_groupby': searchbar_groupby,
            'searchbar_inputs': searchbar_inputs,
            'search_in': search_in,
            'search': search,
            'groupby': groupby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
        })
        return request.render("escalator.portal_my_tickets", values)

    @http.route(['/my/tickets/<int:ticket_id>'], type='http', auth="user", website=True)
    def my_tickets_ticket(self, ticket_id=None, **kw):
        ticket = request.env['escalator_lite.ticket'].browse(ticket_id)
        return request.render("escalator.my_tickets_ticket", {'ticket': ticket})

    @http.route(['/my/public/tickets/<int:ticket_id>'], type='http', auth="public", website=True)
    def my_public_tickets_ticket(self, ticket_id=None, **kw):
        ticket = request.env['escalator_lite.ticket'].browse(ticket_id)
        return request.render("escalator.my_tickets_ticket", {'ticket': ticket})

    @http.route(['/escalator/new'], type='http', auth="public", website=True)
    def ticket_new(self, **kw):
        pri = request.env['escalator_lite.ticket'].fields_get(allfields=['priority'])['priority']['selection']
        pri_default = '1'
        if(request.session.uid):
            # user = request.env.user
            vals = {
                'loggedin': True,
                'priorities': pri,
                'priority_default': pri_default,
            }
        else:
            vals = {
                'loggedin': False,
                'priorities': pri,
                'priority_default': pri_default,
            }

        return request.render("escalator.new_ticket", vals)

    @http.route(['/escalator/close/<int:ticket_id>'], type='http', auth="user", website=True)
    def ticket_close(self, ticket_id=None, **kw):
        """Close a ticket by moving it to the last stage"""
        ticket = request.env['escalator_lite.ticket'].browse(ticket_id)
        if ticket.exists():
            last_stage = request.env['escalator_lite.stage'].search([('last', '=', True)], limit=1)
            if last_stage:
                ticket.write({'stage_id': last_stage.id})
        return request.redirect('/my/tickets')

    @http.route(['/escalator/assign/<int:ticket_id>'], type='http', auth="user", website=True)
    def ticket_assign(self, ticket_id=None, **kw):
        """Assign a ticket to current user"""
        ticket = request.env['escalator_lite.ticket'].browse(ticket_id)
        if ticket.exists():
            ticket.write({'user_id': request.env.user.id})
        return request.redirect('/my/tickets')

    @http.route(['/my/tickets/stats'], type='http', auth="user", website=True)
    def my_tickets_stats(self, **kw):
        """Display ticket statistics for the current user"""
        domain = []
        total_tickets = request.env['escalator_lite.ticket'].search_count(domain)
        open_tickets = request.env['escalator_lite.ticket'].search_count([('is_final_stage', '=', False)])
        closed_tickets = request.env['escalator_lite.ticket'].search_count([('is_final_stage', '=', True)])
        my_tickets = request.env['escalator_lite.ticket'].search_count([('user_id', '=', request.env.user.id)])
        urgent_tickets = request.env['escalator_lite.ticket'].search_count([('priority', '=', '3')])

        values = {
            'page_name': 'ticket_stats',
            'total_tickets': total_tickets,
            'open_tickets': open_tickets,
            'closed_tickets': closed_tickets,
            'my_tickets': my_tickets,
            'urgent_tickets': urgent_tickets,
        }
        return request.render("escalator.portal_ticket_stats", values)

    @http.route(['/escalator/submit'], type='http', auth="public", website=True, csrf=False, methods=['POST'])
    def ticket_submit(self, **post):
        """Handle ticket form submission and return JSON response"""
        try:
            # Clean the form data
            vals = {}
            for field_name in ['name', 'description', 'email_from', 'contact_name', 'priority', 'date_deadline']:
                if post.get(field_name):
                    vals[field_name] = post[field_name]
            
            # Set default priority if not provided
            if 'priority' not in vals:
                vals['priority'] = '1'
            
            # Create the ticket
            ticket = request.env['escalator_lite.ticket'].sudo().create(vals)
            
            # Prepare success response
            response_data = {
                'result': 'success',
                'ticket_id': ticket.id,
                'message': 'Your ticket has been created successfully!',
                'redirect': '/my/tickets' if request.session.uid else '/'
            }
            
            # Return JSON response
            return request.make_response(
                json.dumps(response_data),
                headers=[('Content-Type', 'application/json')]
            )
            
        except Exception as e:
            # Log the error
            import logging
            _logger = logging.getLogger(__name__)
            _logger.error(f"Error creating ticket: {str(e)}")
            
            # Return error response
            error_data = {
                'result': 'error',
                'message': 'An error occurred while creating your ticket. Please try again.'
            }
            
            return request.make_response(
                json.dumps(error_data),
                headers=[('Content-Type', 'application/json')]
            )

