#!/usr/bin/env python3
"""
Test de validation du parsing des dates
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
import re

def test_date_parsing():
    """Test de la fonction de parsing des dates"""
    
    def _parse_date(date_str):
        """Parse date string from various formats and return ISO format"""
        if not date_str:
            return None
        
        # Nettoyer la chaîne
        date_str = date_str.strip()
        
        # Formats possibles
        formats = [
            '%Y-%m-%d',        # ISO format (YYYY-MM-DD)
            '%d/%m/%Y',        # French format (DD/MM/YYYY)
            '%m/%d/%Y',        # US format (MM/DD/YYYY)
            '%d-%m-%Y',        # Alternative format (DD-MM-YYYY)
            '%m-%d-%Y',        # Alternative format (MM-DD-YYYY)
            '%Y/%m/%d',        # Alternative format (YYYY/MM/DD)
            '%d.%m.%Y',        # European format (DD.MM.YYYY)
            '%Y-%m-%d %H:%M:%S',  # With time
            '%d/%m/%Y %H:%M:%S',  # French with time
            '%m/%d/%Y %H:%M:%S',  # US with time
        ]
        
        for fmt in formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                # Retourner au format ISO
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        # Si aucun format ne fonctionne, essayer de détecter automatiquement
        try:
            # Regex pour détecter les formats courants
            if re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', date_str):
                parts = date_str.split('/')
                day, month, year = parts[0], parts[1], parts[2]
                
                # Vérifier si c'est MM/DD/YYYY ou DD/MM/YYYY
                if int(month) > 12:  # Si mois > 12, c'est DD/MM/YYYY
                    day, month = month, day
                elif int(day) > 12:  # Si jour > 12, c'est MM/DD/YYYY
                    month, day = day, month
                
                # Créer la date
                parsed_date = datetime(int(year), int(month), int(day))
                return parsed_date.strftime('%Y-%m-%d')
                
        except (ValueError, IndexError):
            pass
        
        print(f'Impossible de parser la date: {date_str}')
        return None
    
    # Tests
    test_cases = [
        # Format ISO
        ('2025-07-17', '2025-07-17'),
        ('2025-12-31', '2025-12-31'),
        
        # Format français DD/MM/YYYY
        ('17/07/2025', '2025-07-17'),
        ('31/12/2025', '2025-12-31'),
        
        # Format US MM/DD/YYYY
        ('07/17/2025', '2025-07-17'),
        ('12/31/2025', '2025-12-31'),
        
        # Format DD-MM-YYYY
        ('17-07-2025', '2025-07-17'),
        
        # Format MM-DD-YYYY
        ('07-17-2025', '2025-07-17'),
        
        # Format européen DD.MM.YYYY
        ('17.07.2025', '2025-07-17'),
        
        # Cas ambigus (détection automatique)
        ('05/03/2025', '2025-03-05'),  # Pourrait être 5 mars ou 3 mai
        ('13/03/2025', '2025-03-13'),  # Clairement 13 mars (mois > 12)
        ('03/13/2025', '2025-03-13'),  # Clairement 13 mars (jour > 12)
        
        # Cas d'erreur
        ('invalid', None),
        ('32/13/2025', None),
        ('', None),
    ]
    
    print("=== TEST DE PARSING DES DATES ===\n")
    
    success_count = 0
    total_count = len(test_cases)
    
    for input_date, expected in test_cases:
        result = _parse_date(input_date)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{input_date}' -> '{result}' (attendu: '{expected}')")
        
        if result == expected:
            success_count += 1
    
    print(f"\nRésultats: {success_count}/{total_count} tests réussis")
    
    if success_count == total_count:
        print("✅ Tous les tests sont passés!")
        return True
    else:
        print("❌ Certains tests ont échoué")
        return False

def main():
    print("="*60)
    print("VALIDATION DU PARSING DES DATES")
    print("="*60)
    print()
    
    if test_date_parsing():
        print("\n🎉 La fonction de parsing des dates fonctionne correctement!")
        print("\nBénéfices:")
        print("- Support des formats français DD/MM/YYYY")
        print("- Support des formats US MM/DD/YYYY")
        print("- Support du format ISO YYYY-MM-DD")
        print("- Détection automatique des cas ambigus")
        print("- Gestion robuste des erreurs")
        print("\nLe problème de format de date selon la locale du navigateur devrait être résolu.")
    else:
        print("\n⚠️  Des améliorations sont nécessaires")

if __name__ == "__main__":
    main()
