# -*- coding: utf-8 -*-
{
    'name': "Escalator",
    'version': "15.0.1.0.0",
    'author': "Arnold BUKASA",
    'category': "Services/Helpdesk",
    'support': "golubev@svami.in.ua",
    'summary': "Open ticket for unprocessed task with team management",
    'description': """
        Escalator - Helpdesk & Ticket Management
        =====================================
        
        * Gestion des tickets avec équipes et portail web
        * Suivi des étapes de traitement
        * Catégorisation des tickets
        * Automatisation des processus
    """,
    'license': 'LGPL-3',
    'data': [
        'security/escalator_security.xml',
        'security/ir.model.access.csv',
        'views/escalator_tickets.xml',
        'views/escalator_team_views.xml',
        'views/escalator_stage_views.xml',
        'views/escalator_category_views.xml',
        'views/escalator_data.xml',
        'views/escalator_templates.xml',
        'data/escalator_cron.xml',
    ],
    'demo': [
        'demo/escalator_demo.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'depends': [
        'base',
        'mail',
        'portal',
        'hr_expense',
        'web',
    ],
    'application': True,
    'sequence': 1,
    'installable': True,
    'assets': {
        'web.assets_backend': [
            'escalator/static/src/**/*',
        ],
        'web.assets_frontend': [
            'escalator/static/src/**/*',
        ],
    },
}
