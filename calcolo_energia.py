#!/usr/bin/env python3
"""
Script per calcolare l'energia consumata per ogni singola commessa
"""

from db import TelemetriaDB
import json

def calcola_energia_per_commessa():
    """
    Calcola l'energia consumata per ogni commessa.
    Il campo 'potenza_consumata_tx' contiene il progressivo in Wh.
    L'energia consumata si calcola come differenza tra progressivi.
    """
    print("🔋 Calcolo energia per commessa\n")
    
    db = TelemetriaDB()
    
    # Usa la nuova funzione per calcolare l'energia correttamente
    commesse_energia = db.calcola_energia_tutte_commesse()
    
    if not commesse_energia:
        print("❌ Nessun record trovato nel database")
        return
    
    # Mostra i risultati
    print("📊 Energia consumata per commessa:")
    print("-" * 100)
    print(f"{'Commessa':<10} {'Energia (Wh)':<15} {'Energia (kWh)':<15} {'Progressivo':<12} {'Descrizione':<30}")
    print("-" * 100)
    
    totale_energia_wh = 0
    totale_commesse = len(commesse_energia)
    
    # Ordina per energia decrescente
    sorted_commesse = sorted(commesse_energia, 
                            key=lambda x: x['energia_consumata_wh'], 
                            reverse=True)
    
    for commessa_data in sorted_commesse:
        commessa = commessa_data['commessa_tx']
        energia_wh = commessa_data['energia_consumata_wh']
        energia_kwh = commessa_data['energia_consumata_kwh']
        progressivo = commessa_data['progressivo_finale']
        descrizione = commessa_data['descrizione'] or 'Nessuna descrizione'
        
        print(f"{commessa:<10} {energia_wh:<15} {energia_kwh:<15.3f} {progressivo:<12} {descrizione[:30]:<30}")
        totale_energia_wh += energia_wh
    
    totale_energia_kwh = totale_energia_wh / 1000.0
    
    print("-" * 100)
    print(f"{'TOTALE':<10} {totale_energia_wh:<15} {totale_energia_kwh:<15.3f} {'':<12} {totale_commesse} commesse")
    
    # Statistiche aggiuntive
    print(f"\n📈 Statistiche:")
    print(f"• Commesse totali: {totale_commesse}")
    print(f"• Energia totale consumata: {totale_energia_wh} Wh ({totale_energia_kwh:.3f} kWh)")
    print(f"• Energia media per commessa: {totale_energia_kwh/totale_commesse:.3f} kWh")
    
    # Top 5 commesse per energia
    print(f"\n🏆 Top 5 commesse per energia consumata:")
    for i, commessa_data in enumerate(sorted_commesse[:5], 1):
        commessa = commessa_data['commessa_tx']
        energia_kwh = commessa_data['energia_consumata_kwh']
        descrizione = commessa_data['descrizione'] or 'Nessuna descrizione'
        print(f"{i}. Commessa {commessa}: {energia_kwh:.3f} kWh - {descrizione}")
    
    # Mostra dettagli progressivi
    print(f"\n🔍 Dettagli progressivi:")
    print("-" * 80)
    print(f"{'Commessa':<10} {'Progressivo Precedente':<20} {'Progressivo Finale':<20} {'Differenza (Wh)':<15}")
    print("-" * 80)
    
    for commessa_data in sorted_commesse:
        commessa = commessa_data['commessa_tx']
        progressivo_prec = commessa_data['progressivo_precedente']
        progressivo_finale = commessa_data['progressivo_finale']
        differenza = commessa_data['energia_consumata_wh']
        
        print(f"{commessa:<10} {progressivo_prec:<20} {progressivo_finale:<20} {differenza:<15}")

def esporta_energia_json():
    """Esporta i dati dell'energia in formato JSON"""
    print("\n💾 Esportazione dati energia in JSON...")
    
    db = TelemetriaDB()
    commesse_energia = db.calcola_energia_tutte_commesse()
    
    if not commesse_energia:
        print("❌ Nessun record trovato")
        return
    
    # Calcola statistiche per l'export
    totale_energia_wh = sum(c['energia_consumata_wh'] for c in commesse_energia)
    totale_energia_kwh = totale_energia_wh / 1000.0
    
    export_data = {
        'metadata': {
            'totale_commesse': len(commesse_energia),
            'energia_totale_wh': totale_energia_wh,
            'energia_totale_kwh': round(totale_energia_kwh, 3),
            'energia_media_kwh': round(totale_energia_kwh / len(commesse_energia), 3),
            'note': 'Energia calcolata come differenza tra progressivi Wh'
        },
        'commesse': commesse_energia
    }
    
    # Salva in JSON
    with open('energia_per_commessa.json', 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    print("✅ Dati esportati in 'energia_per_commessa.json'")

def main():
    """Funzione principale"""
    print("⚡ Calcolatore Energia per Commessa")
    print("=" * 50)
    
    try:
        calcola_energia_per_commessa()
        esporta_energia_json()
        
        print(f"\n💡 Note importanti:")
        print("• Il campo 'potenza_consumata_tx' contiene il PROGRESSIVO in Wh")
        print("• L'energia consumata si calcola come differenza tra progressivi")
        print("• Ogni record rappresenta una commessa completata")
        print("• Le descrizioni possono essere aggiunte tramite l'interfaccia web")
        print("• Usa l'API /api/commessa/energia/<numero> per calcoli specifici")
        
    except Exception as e:
        print(f"❌ Errore: {e}")

if __name__ == "__main__":
    main()