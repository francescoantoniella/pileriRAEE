from datetime import datetime

def format_timestamp(timestamp_str):
    """
    Converte un timestamp ISO in formato dd/mm/yyyy hh:mm
    """
    try:
        # Rimuovi la 'Z' finale se presente
        if timestamp_str.endswith('Z'):
            timestamp_str = timestamp_str[:-1]
        
        # Parsing del timestamp ISO
        dt = datetime.fromisoformat(timestamp_str)
        
        # Formato italiano: dd/mm/yyyy hh:mm
        return dt.strftime('%d/%m/%Y %H:%M')
    except Exception as e:
        # Se c'è un errore, restituisci il timestamp originale
        return timestamp_str

def format_timestamp_for_display(timestamp_str):
    """
    Versione più robusta per la visualizzazione
    """
    try:
        # Gestisce vari formati di timestamp
        if 'T' in timestamp_str:
            # Formato ISO
            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str[:-1]
            dt = datetime.fromisoformat(timestamp_str)
        else:
            # Altri formati
            dt = datetime.fromisoformat(timestamp_str)
        
        return dt.strftime('%d/%m/%Y %H:%M')
    except:
        return timestamp_str 