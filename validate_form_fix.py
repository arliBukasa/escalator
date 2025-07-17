#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script to validate the website form redirection fix
"""

import sys
import os

def check_controller_setup():
    """Check if the website form controller is properly set up"""
    print("Checking website form controller setup...")
    
    controller_path = os.path.join(os.path.dirname(__file__), 'controllers/website_form.py')
    if os.path.exists(controller_path):
        with open(controller_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        checks = [
            ('ContactController class', 'class ContactController(http.Controller)'),
            ('website_form route', '@http.route(\'/website_form/<string:model_name>\''),
            ('escalator_lite.ticket handling', 'if model_name == \'escalator_lite.ticket\''),
            ('success redirect', 'return request.redirect(\'/escalator/success'),
            ('error redirect', 'return request.redirect(\'/escalator/error'),
            ('success route', '@http.route(\'/escalator/success\''),
            ('error route', '@http.route(\'/escalator/error\''),
        ]
        
        for check_name, check_text in checks:
            if check_text in content:
                print(f"✅ {check_name} - Found")
            else:
                print(f"❌ {check_name} - Missing")
                return False
        
        return True
    else:
        print("❌ website_form.py controller not found")
        return False

def check_templates():
    """Check if success and error templates exist"""
    print("\nChecking templates...")
    
    template_path = os.path.join(os.path.dirname(__file__), 'views/escalator_templates.xml')
    if os.path.exists(template_path):
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        templates = [
            ('Success template', 'id="ticket_success"'),
            ('Error template', 'id="ticket_error"'),
            ('Success page content', 'Your ticket has been created successfully'),
            ('Error page content', 'There was an error creating your ticket'),
        ]
        
        for template_name, template_text in templates:
            if template_text in content:
                print(f"✅ {template_name} - Found")
            else:
                print(f"❌ {template_name} - Missing")
                return False
        
        return True
    else:
        print("❌ escalator_templates.xml not found")
        return False

def check_controller_import():
    """Check if the controller is properly imported"""
    print("\nChecking controller imports...")
    
    init_path = os.path.join(os.path.dirname(__file__), 'controllers/__init__.py')
    if os.path.exists(init_path):
        with open(init_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'website_form' in content:
            print("✅ website_form controller imported")
            return True
        else:
            print("❌ website_form controller not imported")
            return False
    else:
        print("❌ controllers/__init__.py not found")
        return False

def main():
    """Main validation function"""
    print("Website Form Redirection Fix Validation")
    print("=" * 50)
    
    success = True
    
    # Check controller setup
    if not check_controller_setup():
        success = False
    
    # Check templates
    if not check_templates():
        success = False
    
    # Check controller import
    if not check_controller_import():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All validations passed!")
        print("\nChanges made:")
        print("- Modified website_form controller to use redirects instead of JSON")
        print("- Added success page route: /escalator/success")
        print("- Added error page route: /escalator/error")
        print("- Created ticket_success and ticket_error templates")
        print("- Fixed form submission redirection issue")
        print("\nThe form should now properly redirect after submission!")
    else:
        print("❌ Some validations failed!")
        print("Please review and fix the issues above.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
