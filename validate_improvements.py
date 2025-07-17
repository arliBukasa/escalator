# -*- coding: utf-8 -*-
"""
Script de validation des améliorations du module Escalator
Ce script vérifie que toutes les améliorations ont été correctement implémentées
"""

import os
import xml.etree.ElementTree as ET

def check_file_exists(file_path):
    """Vérifie qu'un fichier existe"""
    return os.path.exists(file_path)

def check_xml_valid(file_path):
    """Vérifie qu'un fichier XML est valide"""
    try:
        ET.parse(file_path)
        return True
    except ET.ParseError as e:
        print(f"Erreur XML dans {file_path}: {e}")
        return False

def validate_escalator_improvements():
    """Valide toutes les améliorations du module Escalator"""
    
    base_path = r"c:\Program Files (x86)\Odoo 12.0\server\odoo\addons\escalator"
    
    print("🔍 VALIDATION DES AMÉLIORATIONS DU MODULE ESCALATOR")
    print("=" * 60)
    
    # 1. Vérification des nouveaux fichiers
    print("\n1. Vérification des nouveaux fichiers:")
    new_files = [
        "models/escalator_category.py",
        "models/escalator_sla.py", 
        "views/escalator_category_views.xml",
        "data/escalator_cron.xml",
        "tests/__init__.py",
        "tests/test_escalator.py"
    ]
    
    for file_path in new_files:
        full_path = os.path.join(base_path, file_path)
        status = "✅" if check_file_exists(full_path) else "❌"
        print(f"   {status} {file_path}")
    
    # 2. Vérification des vues XML
    print("\n2. Vérification de la validité XML:")
    xml_files = [
        "views/escalator_tickets.xml",
        "views/escalator_category_views.xml",
        "views/escalator_templates.xml",
        "data/escalator_cron.xml"
    ]
    
    for xml_file in xml_files:
        full_path = os.path.join(base_path, xml_file)
        if check_file_exists(full_path):
            status = "✅" if check_xml_valid(full_path) else "❌"
            print(f"   {status} {xml_file}")
        else:
            print(f"   ❌ {xml_file} (fichier manquant)")
    
    # 3. Vérification du contenu des améliorations
    print("\n3. Vérification des améliorations principales:")
    
    improvements = [
        ("Modèle de catégorie", "models/escalator_category.py"),
        ("Modèle SLA", "models/escalator_sla.py"),
        ("Contrôleur amélioré", "controllers/portal.py"),
        ("Vues de catégorie", "views/escalator_category_views.xml"),
        ("Template de statistiques", "views/escalator_templates.xml"),
        ("Tâche cron", "data/escalator_cron.xml"),
        ("Tests unitaires", "tests/test_escalator.py")
    ]
    
    for improvement, file_path in improvements:
        full_path = os.path.join(base_path, file_path)
        status = "✅" if check_file_exists(full_path) else "❌"
        print(f"   {status} {improvement}")
    
    # 4. Vérification des champs ajoutés dans le modèle ticket
    print("\n4. Vérification des nouveaux champs dans le modèle ticket:")
    
    ticket_model_path = os.path.join(base_path, "models/escalator_ticket.py")
    if check_file_exists(ticket_model_path):
        with open(ticket_model_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        new_fields = [
            "progress",
            "attachment_ids", 
            "category_id",
            "estimated_hours",
            "actual_hours",
            "resolution",
            "is_escalated",
            "escalation_date",
            "resolution_time"
        ]
        
        for field in new_fields:
            status = "✅" if field in content else "❌"
            print(f"   {status} Champ '{field}'")
    
    # 5. Vérification du manifeste
    print("\n5. Vérification du manifeste:")
    
    manifest_path = os.path.join(base_path, "__manifest__.py")
    if check_file_exists(manifest_path):
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest_content = f.read()
            
        required_files = [
            "escalator_category_views.xml",
            "escalator_cron.xml"
        ]
        
        for req_file in required_files:
            status = "✅" if req_file in manifest_content else "❌"
            print(f"   {status} {req_file} dans le manifeste")
    
    print("\n" + "=" * 60)
    print("✨ RÉSUMÉ DES AMÉLIORATIONS APPORTÉES:")
    print("   • Système de progression avec barres colorées")
    print("   • Modèle de catégories hiérarchiques")
    print("   • Système SLA complet")
    print("   • Escalade automatique des tickets")
    print("   • Contrôleur portal amélioré")
    print("   • Templates de statistiques")
    print("   • Tests unitaires")
    print("   • Vues Kanban enrichies")
    print("   • Gestion des pièces jointes")
    print("   • Calculs automatiques de temps")

if __name__ == "__main__":
    validate_escalator_improvements()
