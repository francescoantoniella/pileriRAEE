from opcua import Client, ua
import time
import json
from datetime import datetime
import threading
from data_provider import DataProvider


class OpcuaReader(DataProvider):
    def __init__(self, server_url, tag_names, tag_check, namespace_index=2, tag_prefix="Siemens S7-1200/S7-1500.Tags.", on_change_callback=None, on_read_callback=None, interval=2.0):
        super().__init__(tag_names, tag_check, on_change_callback, on_read_callback, interval)
        self.server_url = server_url
        self.namespace_index = namespace_index
        self.tag_prefix = tag_prefix
        self.client = Client(self.server_url)
        self.tag_nodes = {}
        # Il poller e le richieste web (imposta_commessa) condividono lo stesso client:
        # senza lock uno dei due chiude la sessione dell'altro a metà operazione
        self._io_lock = threading.RLock()

    def connect(self):
        try:
            #print(f"Tentativo di connessione a: {self.server_url}")
            self.client.connect()
            #print("Connesso al server OPC UA")
            
            # Prepara i nodi OPC UA
            for name in self.tag_names:
                node_id_str = f"{self.tag_prefix}{name}"
                try:
                    node = self.client.get_node(ua.NodeId(node_id_str, self.namespace_index))
                    self.tag_nodes[name] = node
                    #print(f"Nodo preparato: {name}")
                except Exception as e:
                    print(f"Errore nella preparazione del nodo {name}: {e}")
                    # Crea un nodo fittizio per evitare errori
                    self.tag_nodes[name] = None
                    
        except Exception as e:
            print(f"Errore nella connessione OPC UA: {e}")
            raise

    def disconnect(self):
        try:
            if hasattr(self, 'client') and self.client:
                self.client.disconnect()
               # print("Disconnesso dal server OPC UA")
        except Exception as e:
            print(f"Errore nella disconnessione OPC UA: {e}")

    def read_once(self):
        with self._io_lock:
            self.connect()
            result = {"timestamp": datetime.now().isoformat() + "Z"}

            # Lettura tutto-o-niente: un tag letto a 0 per errore (es. BadNoCommunication
            # subito dopo la riconnessione) verrebbe scambiato per un cambio di stato commessa
            try:
                for name, node in self.tag_nodes.items():
                    if node is None:
                        raise RuntimeError(f"Nodo {name} non disponibile")
                    try:
                        result[name] = node.get_value()
                    except Exception as e:
                        raise RuntimeError(f"Errore nella lettura del tag {name}: {e}") from e
            finally:
                self.disconnect()
            return result

    def write_tags(self, nuova_commessa, nuovo_cer):
        with self._io_lock:
            try:
                self.connect()
                print(f"Tentativo di scrittura: Commessa={nuova_commessa}, CER={nuovo_cer}")

                for tag, valore in (("Commessa RX", nuova_commessa), ("Codice CER RX", nuovo_cer)):
                    node = self.client.get_node(ua.NodeId(f"{self.tag_prefix}{tag}", self.namespace_index))
                    dv = ua.DataValue(ua.Variant(int(valore), ua.VariantType.UInt32))
                    node.set_attribute(ua.AttributeIds.Value, dv)

                print("Scrittura completata con successo")
                return True

            except Exception as e:
                print(f"Errore nella scrittura dei tag OPC UA: {e}")
                return False
            finally:
                self.disconnect()
