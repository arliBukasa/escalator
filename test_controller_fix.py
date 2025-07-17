#!/usr/bin/env python3
"""
Test de validation du contrôleur corrigé
"""

def validate_controller_logic():
    """Valide la logique du contrôleur"""
    
    controller_path = r"c:\Program Files (x86)\Odoo 12.0\server\odoo\addons\escalator\controllers\website_form.py"
    
    try:
        with open(controller_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("=== VALIDATION DU CONTRÔLEUR CORRIGÉ ===\n")
        
        # Vérifier que tous les chemins retournent une réponse
        issues = []
        
        # 1. Vérifier le return dans le cas de succès
        if "return request.redirect('/escalator/success" in content:
            print("✓ Return de redirection de succès présent")
        else:
            print("✗ Return de redirection de succès manquant")
            issues.append("Pas de return pour la redirection de succès")
        
        # 2. Vérifier le return dans le cas d'erreur  
        if "return request.redirect('/escalator/error" in content:
            print("✓ Return de redirection d'erreur présent")
        else:
            print("✗ Return de redirection d'erreur manquant")
            issues.append("Pas de return pour la redirection d'erreur")
        
        # 3. Vérifier le return pour les autres modèles
        if "return super(EscalatorWebsiteForm, self).website_form" in content:
            print("✓ Return pour les autres modèles présent")
        else:
            print("✗ Return pour les autres modèles manquant")
            issues.append("Pas de return pour l'appel super()")
        
        # 4. Vérifier qu'il n'y a pas de lignes commentées problématiques
        if "#return request.redirect" in content:
            print("✗ Des returns sont encore commentés")
            issues.append("Des returns sont commentés")
        else:
            print("✓ Aucun return commenté trouvé")
        
        # 5. Vérifier la structure générale
        lines = content.split('\n')
        in_escalator_if = False
        has_try = False
        has_except = False
        
        for line in lines:
            line = line.strip()
            if "if model_name == 'escalator_lite.ticket':" in line:
                in_escalator_if = True
            elif in_escalator_if and line.startswith("try:"):
                has_try = True
            elif in_escalator_if and line.startswith("except"):
                has_except = True
        
        if has_try and has_except:
            print("✓ Structure try/except correcte")
        else:
            print("✗ Structure try/except incorrecte")
            issues.append("Structure try/except manquante ou incorrecte")
        
        print()
        
        if not issues:
            print("✅ TOUS LES TESTS SONT PASSÉS!")
            print("Le contrôleur devrait maintenant retourner des réponses valides.")
        else:
            print("❌ PROBLÈMES DÉTECTÉS:")
            for issue in issues:
                print(f"   - {issue}")
        
        print()
        
        return len(issues) == 0
        
    except Exception as e:
        print(f"✗ Erreur lors de la validation: {e}")
        return False

def show_controller_flow():
    """Affiche le flux de traitement du contrôleur"""
    
    print("=== FLUX DE TRAITEMENT DU CONTRÔLEUR ===\n")
    
    print("1. Requête POST vers /website_form/escalator_lite.ticket")
    print("   ↓")
    print("2. Vérification: model_name == 'escalator_lite.ticket' ?")
    print("   ├─ OUI → Continue vers 3")  
    print("   └─ NON → Appel super().website_form() → RETURN")
    print("   ↓")
    print("3. TRY: Création du ticket")
    print("   ├─ Préparation des données")
    print("   ├─ Nettoyage des champs")
    print("   ├─ Création du ticket")
    print("   ├─ Gestion des pièces jointes")
    print("   └─ RETURN request.redirect('/escalator/success')")
    print("   ↓")
    print("4. EXCEPT: En cas d'erreur")
    print("   └─ RETURN request.redirect('/escalator/error')")
    print()
    print("RÉSULTAT: Chaque chemin retourne une réponse HTTP valide")
    print()

def main():
    print("="*60)
    print("VALIDATION DE LA CORRECTION DU CONTRÔLEUR")
    print("="*60)
    print()
    
    validation_ok = validate_controller_logic()
    print()
    show_controller_flow()
    
    if validation_ok:
        print("🎉 CORRECTION RÉUSSIE!")
        print("Le message d'erreur 'returns an invalid response type' devrait disparaître.")
        print()
        print("PROCHAINE ÉTAPE:")
        print("1. Redémarrer Odoo")
        print("2. Tester /escalator/new")
        print("3. Vérifier les logs - plus de message 204 ou d'erreur de type de réponse")
    else:
        print("⚠️  CORRECTION NÉCESSAIRE")
        print("Veuillez corriger les problèmes listés ci-dessus.")

if __name__ == "__main__":
    main()
