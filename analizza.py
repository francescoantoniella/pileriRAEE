import csv
import sys

def analizza_log(file_path):
    try:
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = list(csv.reader(f))
            
            if len(reader) < 2:
                print("Il file non contiene abbastanza dati.")
                return

            # Intestazione e righe dati
            header = reader[0]
            first_row = reader[5]
            last_row = reader[-5]

            # L'ultimo campo è 'Potenza consumata TX' (indice -1) - unità tale che /100 = kWh
            try:
                valore_iniziale = float(first_row[-1])
                valore_finale = float(last_row[-1])
                differenza_kwh = (valore_finale - valore_iniziale) / 100.0
            except ValueError:
                print("Errore: Impossibile convertire i valori in numeri.")
                return
            #ricerca variazioni
#            for row in range(1,len(reader)-2):
#                if      

            # Stampa i risultati (conversione: valore/100 = kWh)
            print(f"--- Analisi File: {file_path} ---")
            print(f"PRIMA RIGA DATA: {', '.join(first_row)}")
            print(f"ULTIMA RIGA DATA: {', '.join(last_row)}")
            print("-" * 40)
            print(f"Energia Iniziale: {valore_iniziale/100:.3f} kWh")
            print(f"Energia Finale:   {valore_finale/100:.3f} kWh")
            print(f"Differenza:       {differenza_kwh:.3f} kWh")

    except FileNotFoundError:
        print(f"Errore: Il file {file_path} non esiste.")

if __name__ == "__main__":
    # Puoi passare il nome del file come argomento: python script.py data_2026-01-15.log
    file_nome = sys.argv[1] if len(sys.argv) > 1 else 'data_2026-01-15.log'
    analizza_log(file_nome)
