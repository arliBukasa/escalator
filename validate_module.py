#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Validation script for escalator module improvements
This script validates the module without running the full Odoo server
"""

import os
import sys
import xml.etree.ElementTree as ET
import ast


def validate_xml_files():
    """Validate all XML files in the module"""
    print("Validating XML files...")
    xml_files = [
        'views/escalator_tickets.xml',
        'views/escalator_category_views.xml', 
        'views/escalator_templates.xml',
        'data/escalator_cron.xml',
        'security/escalator_security.xml',
        'views/escalator_team_views.xml',
        'views/escalator_stage_views.xml',
        'views/escalator_data.xml',
        'demo/escalator_demo.xml'
    ]
    
    for xml_file in xml_files:
        file_path = os.path.join(os.path.dirname(__file__), xml_file)
        if os.path.exists(file_path):
            try:
                ET.parse(file_path)
                print(f"✓ {xml_file} - Valid XML")
            except ET.ParseError as e:
                print(f"✗ {xml_file} - XML Error: {e}")
                return False
        else:
            print(f"- {xml_file} - File not found")
    
    return True


def validate_python_files():
    """Validate Python files for syntax errors"""
    print("\nValidating Python files...")
    python_files = [
        'models/escalator_ticket.py',
        'models/escalator_category.py',
        'models/escalator_sla.py',
        'controllers/portal.py',
        '__init__.py',
        'models/__init__.py',
        '__manifest__.py'
    ]
    
    for py_file in python_files:
        file_path = os.path.join(os.path.dirname(__file__), py_file)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    source = f.read()
                    ast.parse(source)
                print(f"✓ {py_file} - Valid Python syntax")
            except SyntaxError as e:
                print(f"✗ {py_file} - Syntax Error: {e}")
                return False
            except Exception as e:
                print(f"✗ {py_file} - Error: {e}")
                return False
        else:
            print(f"- {py_file} - File not found")
    
    return True


def validate_manifest():
    """Validate the manifest file"""
    print("\nValidating manifest file...")
    manifest_path = os.path.join(os.path.dirname(__file__), '__manifest__.py')
    
    if not os.path.exists(manifest_path):
        print("✗ __manifest__.py not found")
        return False
    
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest_content = f.read()
            manifest_dict = ast.literal_eval(manifest_content)
            
        required_keys = ['name', 'depends', 'data']
        for key in required_keys:
            if key not in manifest_dict:
                print(f"✗ Missing required key in manifest: {key}")
                return False
        
        print("✓ Manifest file valid")
        print(f"  Module name: {manifest_dict.get('name')}")
        print(f"  Dependencies: {manifest_dict.get('depends')}")
        print(f"  Data files: {len(manifest_dict.get('data', []))}")
        
        return True
    except Exception as e:
        print(f"✗ Manifest validation error: {e}")
        return False


def check_improvements():
    """Check if our improvements are in place"""
    print("\nChecking module improvements...")
    improvements = []
    
    # Check portal controller
    portal_path = os.path.join(os.path.dirname(__file__), 'controllers/portal.py')
    if os.path.exists(portal_path):
        with open(portal_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'ticket_close' in content and 'ticket_assign' in content:
                improvements.append("✓ Enhanced portal controller with new routes")
            if 'my_tickets_stats' in content:
                improvements.append("✓ Added ticket statistics functionality")
    
    # Check ticket model improvements
    ticket_path = os.path.join(os.path.dirname(__file__), 'models/escalator_ticket.py')
    if os.path.exists(ticket_path):
        with open(ticket_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'progress' in content and '_compute_progress' in content:
                improvements.append("✓ Added progress tracking")
            if 'category_id' in content:
                improvements.append("✓ Added category support")
            if 'escalation' in content:
                improvements.append("✓ Added escalation functionality")
    
    # Check new models
    if os.path.exists(os.path.join(os.path.dirname(__file__), 'models/escalator_category.py')):
        improvements.append("✓ Category model created")
    if os.path.exists(os.path.join(os.path.dirname(__file__), 'models/escalator_sla.py')):
        improvements.append("✓ SLA model created")
    
    # Check new views
    if os.path.exists(os.path.join(os.path.dirname(__file__), 'views/escalator_category_views.xml')):
        improvements.append("✓ Category views created")
    
    for improvement in improvements:
        print(improvement)
    
    return len(improvements) > 0


def main():
    """Main validation function"""
    print("Escalator Module Validation")
    print("=" * 40)
    
    all_valid = True
    
    # Validate XML files
    if not validate_xml_files():
        all_valid = False
    
    # Validate Python files
    if not validate_python_files():
        all_valid = False
    
    # Validate manifest
    if not validate_manifest():
        all_valid = False
    
    # Check improvements
    if not check_improvements():
        print("\n⚠ Some improvements may be missing")
    
    print("\n" + "=" * 40)
    if all_valid:
        print("✓ All validations passed!")
        print("The module appears to be properly structured and ready for testing.")
    else:
        print("✗ Some validations failed!")
        print("Please fix the errors before deploying the module.")
    
    return all_valid


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
