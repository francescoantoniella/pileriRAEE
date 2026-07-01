import csv

def analizza_cambiamenti(file_path):
    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        ultima_riga = None
        # Lista delle colonne da monitorare (escludiamo il timestamp)
        colonne_dati = [col for col in reader.fieldnames if col != 'timestamp']
        
        print(f"{'Riga':<6} | {'Campo Variato':<30} | {'Variazione'}")
        print("-" * 85)

        for i, riga_corrente in enumerate(reader, start=2):
            if ultima_riga is not None:
                cambiamenti_riga = []
                
                for campo in colonne_dati:
                    v_vecchio = ultima_riga[campo]
                    v_nuovo = riga_corrente[campo]
                    
                    if v_vecchio != v_nuovo:
                        # Formattazione speciale per l'ultima colonna
                        info = f"[{v_vecchio} -> {v_nuovo}]"
                        if campo == "Potenza consumata TX":
                            info = f"*** {info} ***"
                        
                        cambiamenti_riga.append(f"{campo}: {info}")
                
                # Se ci sono stati cambiamenti nei dati (escluso timestamp)
                if cambiamenti_riga:
                    # Stampiamo la prima variazione sulla riga del numero riga
                    # e le altre a capo per leggibilità
                    print(f"{i:<6} | {cambiamenti_riga[0]}")
                    for resto in cambiamenti_riga[1:]:
                        print(f"{' ':<6} | {resto}")
                    print("-" * 85) # Separatore tra blocchi di cambiamento
            
            ultima_riga = riga_corrente

if __name__ == "__main__":
    file_log = "data_2026-01-23.log"
    try:
        analizza_cambiamenti(file_log)
    except FileNotFoundError:
        print(f"Errore: Il file '{file_log}' non è stato trovato.")
