from opcua import Client, ua
import time
import json
from datetime import datetime
import threading
from data_provider import DataProvider


class OpcuaReader(DataProvider):
    def __init__(self, server_url, tag_names, tag_check, namespace_index=2, tag_prefix="Siemens S7-1200/S7-1500.Tags.", on_change_callback=None, interval=1.0):
        super().__init__(tag_names, tag_check, on_change_callback, interval)
        self.server_url = server_url
        self.namespace_index = namespace_index
        self.tag_prefix = tag_prefix
        self.client = Client(self.server_url)
        self.tag_nodes = {}

    def connect(self):
        try:
            print(f"Tentativo di connessione a: {self.server_url}")
            self.client.connect()
            print("Connesso al server OPC UA")
            
            # Prepara i nodi OPC UA
            for name in self.tag_names:
                node_id_str = f"{self.tag_prefix}{name}"
                try:
                    node = self.client.get_node(ua.NodeId(node_id_str, self.namespace_index))
                    self.tag_nodes[name] = node
                    print(f"Nodo preparato: {name}")
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
                print("Disconnesso dal server OPC UA")
        except Exception as e:
            print(f"Errore nella disconnessione OPC UA: {e}")

    def read_once(self):
        result = {"timestamp": datetime.now().isoformat() + "Z"}
        
        for name, node in self.tag_nodes.items():
            try:
                if node is not None:
                    value = node.get_value()
                    result[name] = value
                else:
                    result[name] = 0  # Valore di default se il nodo non è disponibile
            except Exception as e:
                print(f"Errore nella lettura del tag {name}: {e}")
                result[name] = 0  # Valore di default in caso di errore
                
        return result
        
    def write_tags(self, nuova_commessa, nuovo_cer):
        try:
            print(f"Tentativo di scrittura: Commessa={nuova_commessa}, CER={nuovo_cer}")
            
            # Nodi per la scrittura
            commessa_node = self.client.get_node("ns=2;s=Siemens S7-1200/S7-1500.Tags.Commessa RX")
            cer_node = self.client.get_node("ns=2;s=Siemens S7-1200/S7-1500.Tags.Codice CER RX")
            
            # Scrittura commessa
            dv = ua.DataValue()
            dv.Value = ua.Variant(nuova_commessa, ua.VariantType.UInt32)
            commessa_node.set_attribute(ua.AttributeIds.Value, dv)
            
            # Scrittura CER
            dv.Value = ua.Variant(nuovo_cer, ua.VariantType.UInt32)
            cer_node.set_attribute(ua.AttributeIds.Value, dv)
            
            print("Scrittura completata con successo")
            return True
            
        except Exception as e:
            print(f"Errore nella scrittura dei tag OPC UA: {e}")
            return False