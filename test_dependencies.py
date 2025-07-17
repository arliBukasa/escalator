#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script to check model loading dependencies
"""

import sys
import os

def check_model_dependencies():
    """Check if model dependencies are correctly ordered"""
    print("Checking model loading dependencies...")
    
    # Read the __init__.py file to check import order
    init_path = os.path.join(os.path.dirname(__file__), 'models', '__init__.py')
    
    if not os.path.exists(init_path):
        print("✗ models/__init__.py not found")
        return False
    
    with open(init_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    imports = []
    for line in lines:
        line = line.strip()
        if line.startswith('from . import'):
            module_name = line.split('import')[-1].strip()
            imports.append(module_name)
    
    print(f"Import order found: {imports}")
    
    # Check that escalator_ticket comes before escalator_sla
    try:
        ticket_index = imports.index('escalator_ticket')
        sla_index = imports.index('escalator_sla')
        
        if ticket_index < sla_index:
            print("✓ escalator_ticket is loaded before escalator_sla (correct order)")
            return True
        else:
            print("✗ escalator_sla is loaded before escalator_ticket (incorrect order)")
            print("  This can cause model registry issues because escalator_sla inherits from escalator_lite.ticket")
            return False
            
    except ValueError as e:
        print(f"✗ Missing required model import: {e}")
        return False

def check_inheritance_structure():
    """Check for potential circular inheritance issues"""
    print("\nChecking inheritance structure...")
    
    # Check escalator_sla.py for inheritance
    sla_path = os.path.join(os.path.dirname(__file__), 'models', 'escalator_sla.py')
    
    if os.path.exists(sla_path):
        with open(sla_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "_inherit = 'escalator_lite.ticket'" in content:
            print("✓ Found TicketInheritSLA class inheriting from escalator_lite.ticket")
            print("  This requires escalator_ticket to be loaded first")
        else:
            print("- No inheritance from escalator_lite.ticket found in escalator_sla.py")
    
    return True

def main():
    """Main validation function"""
    print("Model Dependency Validation")
    print("=" * 40)
    
    success = True
    
    # Check model dependencies
    if not check_model_dependencies():
        success = False
    
    # Check inheritance structure
    if not check_inheritance_structure():
        success = False
    
    print("\n" + "=" * 40)
    if success:
        print("✓ Model dependencies are correctly ordered!")
        print("The model registry error should be resolved.")
    else:
        print("✗ Model dependency issues found!")
        print("Please fix the import order or inheritance structure.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
