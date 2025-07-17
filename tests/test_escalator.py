# -*- coding: utf-8 -*-
# Test script for Escalator module

import datetime
import logging
from odoo.tests.common import TransactionCase

class TestEscalatorTicket(TransactionCase):

    def setUp(self):
        super(TestEscalatorTicket, self).setUp()
        
        # Create test data
        self.stage_new = self.env['escalator_lite.stage'].create({
            'name': 'New',
            'sequence': 1,
        })
        
        self.stage_in_progress = self.env['escalator_lite.stage'].create({
            'name': 'In Progress',
            'sequence': 2,
        })
        
        self.stage_done = self.env['escalator_lite.stage'].create({
            'name': 'Done',
            'sequence': 3,
            'last': True,
        })
        
        self.test_user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'testuser',
            'email': 'test@example.com',
        })
        
        self.test_partner = self.env['res.partner'].create({
            'name': 'Test Customer',
            'email': 'customer@example.com',
        })

    def test_ticket_creation(self):
        """Test basic ticket creation"""
        ticket = self.env['escalator_lite.ticket'].create({
            'name': 'Test Ticket',
            'description': 'This is a test ticket',
            'partner_id': self.test_partner.id,
            'user_id': self.test_user.id,
            'priority': '1',
        })
        
        self.assertTrue(ticket.id)
        self.assertEqual(ticket.name, 'Test Ticket')
        self.assertEqual(ticket.partner_id.id, self.test_partner.id)
        
    def test_progress_calculation(self):
        """Test progress calculation based on stages"""
        ticket = self.env['escalator_lite.ticket'].create({
            'name': 'Progress Test Ticket',
            'stage_id': self.stage_new.id,
        })
        
        # Check initial progress
        self.assertGreaterEqual(ticket.progress, 0)
        
        # Move to in progress
        ticket.write({'stage_id': self.stage_in_progress.id})
        self.assertGreater(ticket.progress, 0)
        
        # Move to done
        ticket.write({'stage_id': self.stage_done.id})
        self.assertGreaterEqual(ticket.progress, 66)  # Should be at least 66% for last stage

    def test_escalation(self):
        """Test ticket escalation functionality"""
        ticket = self.env['escalator_lite.ticket'].create({
            'name': 'Escalation Test Ticket',
            'date_deadline': datetime.datetime.now() - datetime.timedelta(hours=1),  # Overdue
        })
        
        # Initially not escalated
        self.assertFalse(ticket.is_escalated)
        
        # Test escalation
        ticket.escalate_ticket()
        
        # Should be escalated now
        self.assertTrue(ticket.is_escalated)
        self.assertEqual(ticket.priority, '3')  # Should be urgent

    def test_sla_assignment(self):
        """Test SLA assignment to tickets"""
        # Create a category first
        category = self.env['escalator_lite.category'].create({
            'name': 'Test Category',
        })
        
        # Create an SLA
        sla = self.env['escalator_lite.sla'].create({
            'name': 'Standard SLA',
            'priority': '1',
            'response_time': 4.0,
            'resolution_time': 24.0,
            'category_ids': [(6, 0, [category.id])],
        })
        
        # Create ticket with category
        ticket = self.env['escalator_lite.ticket'].create({
            'name': 'SLA Test Ticket',
            'category_id': category.id,
            'priority': '1',
        })
        
        # SLA should be assigned
        self.assertEqual(ticket.sla_id.id, sla.id)

    def test_category_hierarchy(self):
        """Test category hierarchy functionality"""
        parent_category = self.env['escalator_lite.category'].create({
            'name': 'Parent Category',
        })
        
        child_category = self.env['escalator_lite.category'].create({
            'name': 'Child Category',
            'parent_id': parent_category.id,
        })
        
        # Test name_get for hierarchical display
        name_result = child_category.name_get()
        self.assertIn('Parent Category / Child Category', name_result[0][1])

if __name__ == '__main__':
    # This would be run by Odoo's test framework
    pass
