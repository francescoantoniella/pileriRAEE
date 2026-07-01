from abc import ABC, abstractmethod
import threading
import time
from datetime import datetime
import json
import os

class DataProvider(ABC):
    """Interfaccia comune per i provider di dati"""
    
    def __init__(self, tag_names, tag_check, on_change_callback=None, on_read_callback=None, interval=1.0):
        self.tag_names = tag_names
        self.tag_check = tag_check
        self.on_change_callback = on_change_callback
        self.on_read_callback = on_read_callback
        self.interval = interval
        self.running = False
        self.last_values = {}
        self.actual_values = {}
        self.lock = threading.Lock()
    
    @abstractmethod
    def connect(self):
        """Connette al provider di dati"""
        pass
    
    @abstractmethod
    def disconnect(self):
        """Disconnette dal provider di dati"""
        pass
    
    @abstractmethod
    def read_once(self):
        """Legge una volta i dati"""
        pass
    
    @abstractmethod
    def write_tags(self, commessa, cer):
        """Scrive i tag (se supportato)"""
        pass
    
    def start_polling(self):
        """Avvia il polling dei dati"""
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
    
    def stop_polling(self):
        """Ferma il polling dei dati"""
        self.running = False
        if hasattr(self, "_thread"):
            self._thread.join()
    
    def _poll_loop(self):
        """Loop principale per il polling"""
        while self.running:
            try:
                new_data = self.read_once()
                if self.on_read_callback:
                    print("Read callback")
                    self.on_read_callback(new_data) 
                else: 
                    print("No read callback")
                with self.lock:
                    self.actual_values = new_data
                    changes = {}

                    for key, val in self.actual_values.items():
                        if key not in self.last_values or (self.last_values[key] != val and key in self.tag_check):
                            changes[key] = val

                    if changes and self.on_change_callback:
                        self.on_change_callback(self.actual_values, self.last_values)

                    self.last_values = self.actual_values.copy()
                    
            except Exception as e:
                print(f"Errore durante il polling: {e}")
                
            time.sleep(self.interval)
    
    def get_latest_data(self):
        """Restituisce i dati più recenti"""
        with self.lock:
            return self.actual_values.copy()


class StandaloneDataProvider(DataProvider):
    """Provider di dati standalone - nessuna connessione OPC UA"""
    
    def __init__(self, tag_names, tag_check, on_change_callback=None, on_read_callback=None, interval=1.0):
        super().__init__(tag_names, tag_check, on_change_callback, on_read_callback, interval)
        print("Modalità standalone: nessuna connessione OPC UA richiesta")
    
    def connect(self):
        """Nessuna connessione richiesta in modalità standalone"""
        print("Modalità standalone attivata - server funzionante senza OPC UA")
    
    def disconnect(self):
        """Nessuna disconnessione richiesta"""
        print("Disconnessione dalla modalità standalone")
    
    def read_once(self):
        """Restituisce dati vuoti - nessun polling OPC UA"""
        return {
            "timestamp": datetime.now().isoformat() + "Z",
            "Commessa RX": 0,
            "Codice CER RX": 0,
            "Codice CER TX": 0,
            "Commessa TX": 0,
            "Ore totali commessa TX": 0,
            "Minuti totali commessa TX": 0,
            "Ore lavorate commessa TX": 0,
            "Minuti lavorati commessa TX": 0,
            "Potenza consumata TX": 0
        }
    
    def write_tags(self, commessa, cer):
        """Nessuna scrittura in modalità standalone"""
        print(f"Modalità standalone: simulazione scrittura Commessa={commessa}, CER={cer}")
        return True 
