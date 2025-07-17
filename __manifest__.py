# -*- coding: utf-8 -*-
{
    'name': "escalator",
    'version': "1.1.1",
    'author': "Arnold BUKASA",
    'category': "Tools",
    'support': "golubev@svami.in.ua",
    'summary': "open ticket for unproccessed task",
    'description': """
        Easy to use escalator
        with teams and website portal
    """,
    'license':'LGPL-3',
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
    'depends': ['base', 'mail', 'portal','hr_expense'],
    'application': True,
    'sequence':1,
}
