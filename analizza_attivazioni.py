import csv
import sys
from datetime import datetime

def analizza_attivazioni(file_path):
    try:
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = list(csv.reader(f))
            if not reader: return

            attivazioni = []
            in_attivazione = False
            start_time = None
            start_val = None
            last_val = None
            last_ts = None

            for row in reader:
                if len(row) < 10: continue # Salta righe corrotte
                
                try:
                    # Parsing timestamp e valore (convertito in kWh: valore/100)
                    curr_ts = datetime.strptime(row[0].split('.')[0], "%Y-%m-%dT%H:%M:%S")
                    curr_val = float(row[-1]) / 100
                except (ValueError, IndexError):
                    continue

                if start_val is None:
                    start_val = curr_val
                    last_val = curr_val
                    last_ts = curr_ts
                    continue

                # Se il valore aumenta, il motore è (o si è appena) acceso
                if curr_val > last_val:
                    if not in_attivazione:
                        in_attivazione = True
                        start_time = last_ts # L'attivazione è iniziata all'ultimo timestamp stabile
                        start_val_att = last_val
                
                # Se il valore è fermo ma eravamo in attivazione, il motore si è spento
                elif curr_val == last_val and in_attivazione:
                    durata = (last_ts - start_time).total_seconds()
                    consumo = last_val - start_val_att
                    
                    # Filtro opzionale: registra solo se il consumo è rilevante (> 0)
                    if consumo > 0.02:
                        attivazioni.append({
                            'inizio': start_time,
                            'fine': last_ts,
                            'durata': durata,
                            'consumo': consumo
                        })
                    
                    in_attivazione = False

                last_val = curr_val
                last_ts = curr_ts

            # Stampa Risultati
            print(f"{'INIZIO':<20} | {'DURATA (sec)':<12} | {'CONSUMO (kWh)':<15}")
            print("-" * 55)
            
            tot_consumo = 0
            for a in attivazioni:
                print(f"{a['inizio'].strftime('%H:%M:%S'):<20} | {a['durata']:<12.1f} | {a['consumo']:<15.3f}")
                tot_consumo += a['consumo']

            print("-" * 55)
            print(f"Numero totale attivazioni: {len(attivazioni)}")
            print(f"Consumo totale attivazioni: {tot_consumo:.3f} kWh")

    except FileNotFoundError:
        print(f"Errore: File {file_path} non trovato.")

if __name__ == "__main__":
    file_nome = sys.argv[1] if len(sys.argv) > 1 else 'data_2026-02-09.log'
    analizza_attivazioni(file_nome)
