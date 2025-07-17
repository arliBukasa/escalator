#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script to validate the stage_id.last fix
"""

import sys
import os
import xml.etree.ElementTree as ET

def check_stage_references():
    """Check for remaining stage_id.last references that could cause issues"""
    print("Checking for problematic stage_id.last references...")
    
    files_to_check = [
        'views/escalator_tickets.xml',
        'controllers/portal.py',
        'models/escalator_ticket.py',
        'models/escalator_sla.py'
    ]
    
    issues_found = []
    
    for file_path in files_to_check:
        full_path = os.path.join(os.path.dirname(__file__), file_path)
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    if 'stage_id.last' in line:
                        # Check if this is in a problematic context
                        if any(keyword in line for keyword in ['attrs=', 'domain=[', 'search([']):
                            context = line.strip()
                            if 'compute' not in context and '@api.depends' not in context:
                                issues_found.append(f"{file_path}:{line_num} - {context}")
    
    if issues_found:
        print("❌ Found potentially problematic stage_id.last references:")
        for issue in issues_found:
            print(f"  {issue}")
        return False
    else:
        print("✅ No problematic stage_id.last references found")
        return True

def check_is_final_stage_usage():
    """Check that is_final_stage is properly used"""
    print("\nChecking is_final_stage field usage...")
    
    # Check that the field is defined in the model
    ticket_model_path = os.path.join(os.path.dirname(__file__), 'models/escalator_ticket.py')
    if os.path.exists(ticket_model_path):
        with open(ticket_model_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'is_final_stage = fields.Boolean' in content:
                print("✅ is_final_stage field is defined")
            else:
                print("❌ is_final_stage field not found")
                return False
            
            if '_compute_is_final_stage' in content:
                print("✅ _compute_is_final_stage method found")
            else:
                print("❌ _compute_is_final_stage method not found")
                return False
    
    # Check that the field is used in the view
    view_path = os.path.join(os.path.dirname(__file__), 'views/escalator_tickets.xml')
    if os.path.exists(view_path):
        with open(view_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'is_final_stage' in content:
                print("✅ is_final_stage is used in views")
            else:
                print("❌ is_final_stage not found in views")
                return False
    
    return True

def validate_xml_syntax():
    """Validate XML syntax for ticket views"""
    print("\nValidating XML syntax...")
    
    xml_file = os.path.join(os.path.dirname(__file__), 'views/escalator_tickets.xml')
    if os.path.exists(xml_file):
        try:
            ET.parse(xml_file)
            print("✅ escalator_tickets.xml is valid")
            return True
        except ET.ParseError as e:
            print(f"❌ XML parsing error in escalator_tickets.xml: {e}")
            return False
    else:
        print("❌ escalator_tickets.xml not found")
        return False

def main():
    """Main validation function"""
    print("Stage Field Reference Validation")
    print("=" * 50)
    
    success = True
    
    # Check for problematic stage_id.last references
    if not check_stage_references():
        success = False
    
    # Check is_final_stage usage
    if not check_is_final_stage_usage():
        success = False
    
    # Validate XML syntax
    if not validate_xml_syntax():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All validations passed!")
        print("The 'Unknown field stage_id.last in domain' error should be resolved.")
        print("\nChanges made:")
        print("- Replaced stage_id.last with is_final_stage in views")
        print("- Added is_final_stage as invisible field in form view")
        print("- Updated controller and model references")
    else:
        print("❌ Some validations failed!")
        print("Please review and fix the issues above.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
