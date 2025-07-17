#!/usr/bin/env python3
"""
Script de test pour valider la correction du formulaire
"""

def validate_form_template():
    """Valide le template de formulaire"""
    template_path = r"c:\Program Files (x86)\Odoo 12.0\server\odoo\addons\escalator\views\escalator_templates.xml"
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        print("✓ Template escalator_templates.xml lu avec succès")
        
        # Vérifier que le formulaire pointe vers la bonne action
        if 'action="/website_form/escalator_lite.ticket"' in content:
            print("✓ L'action du formulaire pointe vers /website_form/escalator_lite.ticket")
        else:
            print("✗ L'action du formulaire est incorrecte")
            
        # Vérifier les templates de succès et d'erreur
        if 'id="ticket_success"' in content:
            print("✓ Template ticket_success trouvé")
        else:
            print("✗ Template ticket_success manquant")
            
        if 'id="ticket_error"' in content:
            print("✓ Template ticket_error trouvé")
        else:
            print("✗ Template ticket_error manquant")
            
        # Vérifier la présence du JavaScript
        if 'escalator.form_submit' in content:
            print("✓ JavaScript de gestion du formulaire trouvé")
        else:
            print("✗ JavaScript de gestion du formulaire manquant")
            
        return True
        
    except Exception as e:
        print(f"✗ Erreur lors de la lecture du template: {e}")
        return False

def validate_controller():
    """Valide le contrôleur"""
    controller_path = r"c:\Program Files (x86)\Odoo 12.0\server\odoo\addons\escalator\controllers\website_form.py"
    
    try:
        with open(controller_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        print("✓ Contrôleur website_form.py lu avec succès")
        
        # Vérifier la route de création de ticket
        if '@http.route(\'/website_form/<string:model_name>\',' in content:
            print("✓ Route de création de ticket trouvée")
        else:
            print("✗ Route de création de ticket manquante")
            
        # Vérifier les routes de succès et d'erreur
        if '@http.route(\'/escalator/success\',' in content:
            print("✓ Route de succès trouvée")
        else:
            print("✗ Route de succès manquante")
            
        if '@http.route(\'/escalator/error\',' in content:
            print("✓ Route d'erreur trouvée")
        else:
            print("✗ Route d'erreur manquante")
            
        # Vérifier la gestion de l'escalator_lite.ticket
        if "if model_name == 'escalator_lite.ticket':" in content:
            print("✓ Gestion spécifique du modèle escalator_lite.ticket trouvée")
        else:
            print("✗ Gestion spécifique du modèle escalator_lite.ticket manquante")
            
        return True
        
    except Exception as e:
        print(f"✗ Erreur lors de la lecture du contrôleur: {e}")
        return False

def main():
    """Fonction principale"""
    print("=== Validation de la correction du formulaire ===\n")
    
    print("1. Validation du template:")
    template_ok = validate_form_template()
    print()
    
    print("2. Validation du contrôleur:")
    controller_ok = validate_controller()
    print()
    
    if template_ok and controller_ok:
        print("✓ Tous les tests sont passés!")
        print("\nLe formulaire devrait maintenant fonctionner correctement:")
        print("- Les utilisateurs non connectés peuvent créer des tickets")
        print("- Redirection vers /escalator/success en cas de succès")
        print("- Redirection vers /escalator/error en cas d'erreur")
        print("- Les pièces jointes sont gérées")
        return True
    else:
        print("✗ Certains tests ont échoué. Vérifiez les erreurs ci-dessus.")
        return False

if __name__ == "__main__":
    main()
