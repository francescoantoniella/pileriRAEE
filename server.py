from bottle import Bottle, run, template, static_file, request, TEMPLATE_PATH
from db import TelemetriaDB
import datetime
import os
import sys
from opcua_reader import OpcuaReader
from data_provider import StandaloneDataProvider
import time
import threading
from config import *
from dynamic_config import load_config, save_config, get_config_value, set_config_value
from utils import format_timestamp_for_display
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT

TEMPLATE_PATH.append(os.path.abspath("./templates"))

app = Bottle()
db = TelemetriaDB(DATABASE_PATH)

# Variabile globale per il provider di dati
poller = None
poller_thread = None
poller_running = False

import csv
def datalog(data):
    # Ottiene la data odierna nel formato ANNO-MESE-GIORNO
    data_oggi = datetime.datetime.now().strftime("%Y-%m-%d")
    # Crea il nome del file dinamicamente
    file_path = f"data_{data_oggi}.log"

    # Definiamo l'ordine dei campi (le chiavi del dizionario)
    fieldnames = [
        'timestamp', 'Commessa RX', 'Codice CER RX', 'Codice CER TX', 
        'Commessa TX', 'Ore totali commessa TX', 'Minuti totali commessa TX', 
        'Ore lavorate commessa TX', 'Minuti lavorati commessa TX', 'Potenza consumata TX'
    ]
    
    # Controlliamo se il file esiste già e se ha una dimensione > 0
    file_exists = os.path.isfile(file_path) and os.path.getsize(file_path) > 0

    with open(file_path, mode='a', newline='', encoding='utf-8') as file:
        # DictWriter usa le chiavi del dizionario per scrivere nelle colonne giuste
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        # Se il file è vuoto o non esiste, scrive l'intestazione
        if not file_exists:
            writer.writeheader()
        
        # Scrive la riga con i dati del dizionario
        writer.writerow(data)

    # cerca se c'è una commessa in preparazione
    ultimi = db.leggi_ultimi(1)  
    if ultimi:
       ultima_commessa_tx = data.get('commessa_tx', 0)
       ultima_commessa_rx = data.get('commessa_rx', 0)
       ultima_cer_rx = data.get('codice_cer_rx', 0)
       energia_attuale = data.get("Potenza consumata TX", 0)
       print("---->",ultima_commessa_tx,' ',ultima_commessa_rx, ' ', energia_attuale)
       # Invia i dati al PLC
       if ultima_commessa_rx>0 and ultima_commessa_tx==0 :
           success = poller.write_tags(ultima_commessa_rx, ultima_cer_rx)
           if not success:
               return {"success": False, "error": "Errore nell'invio al PLC"}
           else:
               timestamp = datetime.datetime.now().isoformat()
               record_data = {
                    'timestamp': timestamp,
                    'Commessa RX': ultima_commessa_rx,
                    'Codice CER RX': ultima_cer_rx,
                    'Codice CER TX': ultima_cer_rx,
                    'Commessa TX': ultima_commessa_rx,
                    'Ore totali commessa TX': 0,
                    'Minuti totali commessa TX': 0,
                    'Ore lavorate commessa TX': 0,
                    'Minuti lavorati commessa TX': 0,
                    'Potenza consumata TX': energia_attuale or 0,
                    'Descrizione commessa': f"",
                    'stato_lavorazione': 'preparazione'
                }
               db.insert_record(record_data)



def create_data_provider(mode=None):
    """Crea il provider di dati appropriato"""
    config = load_config()
    
    if mode is None:
        mode = config.get("mode", "opcua")
    
    print(f"Creazione provider per modalità: {mode}")
    
    if mode == "opcua":
        print("Tentativo di connessione OPC UA...")
        return OpcuaReader(
            server_url=config.get("opcua_server_url", OPCUA_SERVER_URL),
            tag_names=TAG_LIST,
            tag_check=TAG_CHECK,
            namespace_index=config.get("opcua_namespace_index", OPCUA_NAMESPACE_INDEX),
            tag_prefix=config.get("opcua_tag_prefix", OPCUA_TAG_PREFIX),
            on_change_callback=on_change,
            on_read_callback=datalog,
            interval=POLLING_INTERVAL
        )
    else:
        print("Modalità standalone: nessuna connessione OPC UA")
        return StandaloneDataProvider(
            tag_names=TAG_LIST,
            tag_check=TAG_CHECK,
            on_change_callback=on_change,
            interval=POLLING_INTERVAL
        )

def start_poller_in_background(mode=None, max_retries=None, retry_delay=None):
    """Avvia il poller in un thread separato con retry automatico"""
    global poller, poller_thread, poller_running
    
    print(f"Avvio poller in background, modalità: {mode}")
    
    # Imposta poller_running a True per permettere l'avvio
    poller_running = True
    
    # Usa i valori di default se non specificati
    if max_retries is None:
        max_retries = POLLER_MAX_RETRIES
    if retry_delay is None:
        retry_delay = POLLER_RETRY_DELAY
    
    def poller_worker():
        global poller_running
        retry_count = 0
        
        print("🔄 Poller worker avviato")
        print(f"poller_running: {poller_running}")
        print(f"max_retries: {max_retries}")
        
        while poller_running and retry_count < max_retries:
            try:
                #print(f"Tentativo di connessione (tentativo {retry_count + 1})...")
                #poller.connect()
                #print("Connessione riuscita, avvio polling...")
                retry_count=0
                poller.start_polling()
                poller_running = True
                print(f"Provider di dati avviato (tentativo {retry_count + 1})")
                
                # Mantieni il thread attivo
                while poller_running:
                    #print("🔄 Poller worker in esecuzione")
                    time.sleep(1)
                    
            except Exception as e:
                print(f"Errore nel provider di dati (tentativo {retry_count + 1}): {e}")
                import traceback
                traceback.print_exc()
                #poller_running = False
                retry_count += 1
                
                print(f"Riprovo tra {retry_delay} secondi...")
                time.sleep(retry_delay)
    
    try:
        print("Creazione provider di dati...")
        poller = create_data_provider(mode)
        print("Provider creato, avvio thread...")
        poller_thread = threading.Thread(target=poller_worker, daemon=True)
        poller_thread.start()
        print("Thread avviato con successo")
        return True
    except Exception as e:
        print(f"Errore nell'avvio del provider di dati: {e}")
        import traceback
        traceback.print_exc()
        return False

def stop_poller():
    """Ferma il poller"""
    global poller_running, poller, poller_thread
    
    poller_running = False
    
    if poller:
        try:
            poller.stop_polling()
            #poller.disconnect()
        except Exception as e:
            print(f"Errore nella disconnessione del poller: {e}")
    
    if poller_thread and poller_thread.is_alive():
        poller_thread.join(timeout=5)

def generate_pdf_report(commesse, titolo, tipo_report, statistiche=None):
    """Genera un PDF del report"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    story = []
    
    # Stili
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    # Titolo
    story.append(Paragraph(titolo, title_style))
    story.append(Spacer(1, 20))
    
    # Statistiche se disponibili
    if statistiche:
        stats_data = [
            ['Statistica', 'Valore'],
            ['Record Totali', str(statistiche['totale_record'])],
            ['Commesse Uniche', str(statistiche['commesse_uniche'])],
            ['Ore Lavorate', str(statistiche['ore_totali_lavorate'])],
            ['Minuti Lavorati', str(statistiche['minuti_totali_lavorati'])],
            ['Energia Totale (kWh)', str(statistiche['energia_totale_consumata'])],
            ['Energia Media (kWh)', f"{statistiche['energia_media_consumata']:.1f}"]
        ]
        
        stats_table = Table(stats_data, colWidths=[2*inch, 1.5*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(Paragraph("Statistiche", styles['Heading2']))
        story.append(stats_table)
        story.append(Spacer(1, 20))
    
    # Tabella dati
    if commesse:
        # Header
        headers = ['Ora Chiusura', 'Commessa', 'CER', 'Descrizione', 'Ore Totali', 'Minuti Totali', 
                  'Ore Lavorate', 'Minuti Lavorati', 'Energia (kWh)']
        
        # Dati
        data = [headers]
        for riga in commesse:
            # Formatta il timestamp per il PDF
            timestamp_formatted = format_timestamp_for_display(riga['timestamp'])
            data.append([
                timestamp_formatted,
                str(riga['commessa_tx']),
                str(riga['codice_cer_tx']),
                str(riga.get('descrizione_commessa', '')),
                str(riga['ore_totali_commessa_tx']),
                str(riga['minuti_totali_commessa_tx']),
                str(riga['ore_lavorate_commessa_tx']),
                str(riga['minuti_lavorati_commessa_tx']),
                str(riga['potenza_consumata_tx'])
            ])
        
        # Crea tabella
        table = Table(data, colWidths=[1.2*inch, 0.8*inch, 0.8*inch, 1.2*inch, 
                                      0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(Paragraph("Dettagli Record", styles['Heading2']))
        story.append(table)
    else:
        story.append(Paragraph("Nessun dato disponibile per questo periodo", styles['Normal']))
    
    # Footer
    story.append(Spacer(1, 20))
    story.append(Paragraph(f"Generato il: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", 
                          styles['Normal']))
    
    # Genera PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

def generate_energy_pdf_report(report_data, titolo):
    """Genera PDF per report energetici (settimanale/mensile/annuale)"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    story = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'EnergyTitle', parent=styles['Heading1'], fontSize=16, spaceAfter=20, alignment=TA_CENTER
    )

    story.append(Paragraph(titolo, title_style))
    story.append(Spacer(1, 12))

    # Tabella statistiche principali
    stats_data = [
        ['Metrica', 'Valore'],
        ['Energia Totale (kWh)', f"{report_data.get('energia_totale_kwh', 0):.3f}"],
        ['Energia Lavorazioni (kWh)', f"{report_data.get('energia_lavorazioni_kwh', 0):.3f}"],
        ['Energia Standby (kWh)', f"{report_data.get('energia_standby_kwh', 0):.3f}"],
        ['Commesse Completate', str(report_data.get('commesse_completate', 0))],
        ['Prima Lettura (Wh)', str(report_data.get('prima_lettura_wh', 0))],
        ['Ultima Lettura (Wh)', str(report_data.get('ultima_lettura_wh', 0))],
        ['Totale Letture', str(report_data.get('totale_letture', 0))],
    ]

    stats_table = Table(stats_data, colWidths=[2.5*inch, 2*inch])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    story.append(stats_table)
    story.append(Spacer(1, 16))

    # Dettaglio commesse (se presente)
    commesse = report_data.get('commesse_dettaglio') or []
    if commesse:
        headers = ['Timestamp', 'Commessa', 'Energia (Wh)', 'Energia (kWh)', 'Descrizione']
        data = [headers]
        for c in commesse:
            energia_wh = c.get('energia_consumata_wh', 0)
            data.append([
                str(c.get('timestamp', '')),
                str(c.get('commessa_tx', '')),
                str(energia_wh),
                f"{energia_wh/RAW_TO_KWH:.3f}",
                str(c.get('descrizione_commessa', ''))
            ])

        table = Table(data, colWidths=[1.5*inch, 0.9*inch, 1.1*inch, 1.1*inch, 2.3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        story.append(Paragraph('Dettaglio Commesse', styles['Heading2']))
        story.append(table)

    doc.build(story)
    buffer.seek(0)
    return buffer

@app.route('/')
def home():
    """Serve il frontend statico Angular.js"""
    return static_file('index.html', root='./static')

@app.route('/report/giornaliero')
def report_giornaliero():
    data = request.query.data or datetime.date.today().isoformat()
    commesse = db.report_giornaliero(data)
    
    # Formatta i timestamp per la visualizzazione
    for commessa in commesse:
        if 'timestamp' in commessa:
            commessa['timestamp_formatted'] = format_timestamp_for_display(commessa['timestamp'])
    
    return template("report", commesse=commesse, titolo=f"Report {data}")

@app.route('/report/mensile')
def report_mensile():
    anno = int(request.query.anno or datetime.date.today().year)
    mese = int(request.query.mese or datetime.date.today().month)
    commesse = db.report_mensile(anno, mese)
    statistiche = db.statistiche_mensili(anno, mese)
    
    # Formatta i timestamp per la visualizzazione
    for commessa in commesse:
        if 'timestamp' in commessa:
            commessa['timestamp_formatted'] = format_timestamp_for_display(commessa['timestamp'])
    
    # Nome del mese
    nomi_mesi = [
        "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
        "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"
    ]
    nome_mese = nomi_mesi[mese - 1]
    
    return template("report_mensile", 
                   commesse=commesse, 
                   statistiche=statistiche,
                   anno=anno, 
                   mese=mese, 
                   nome_mese=nome_mese,
                   titolo=f"Report Mensile {nome_mese} {anno}")

@app.route('/report/annuale')
def report_annuale():
    anno = int(request.query.anno or datetime.date.today().year)
    commesse = db.report_annuale(anno)
    statistiche = db.statistiche_annuali(anno)
    
    # Formatta i timestamp per la visualizzazione
    for commessa in commesse:
        if 'timestamp' in commessa:
            commessa['timestamp_formatted'] = format_timestamp_for_display(commessa['timestamp'])
    
    return template("report_annuale", 
                   commesse=commesse, 
                   statistiche=statistiche,
                   anno=anno,
                   titolo=f"Report Annuale {anno}")

@app.route('/static/<filename>')
def serve_static(filename):
    return static_file(filename, root="./static")

@app.route('/api/commesse/recenti')
def api_recenti():
    """API per tutte le commesse con stato"""
    try:
        # Mostra tutti i record senza limitazioni
        commesse = db.leggi_tutti_con_stato(1000)  # Numero molto alto per includere tutti i record
        # Formatta i timestamp per la visualizzazione e calcola l'energia
        for commessa in commesse:
            if 'timestamp' in commessa:
                commessa['timestamp_formatted'] = format_timestamp_for_display(commessa['timestamp'])
            
            # Calcola l'energia per questa commessa
            commessa_tx = commessa.get('commessa_tx')
            if commessa_tx:
                energia_data = db.calcola_energia_commessa(commessa_tx)
                if energia_data:
                    commessa['energia_calcolata_kwh'] = round(energia_data['energia_consumata_kwh'], 3)
                    commessa['progressivo_wh'] = energia_data['progressivo_finale']
                    commessa['energia_iniziale_wh'] = energia_data['energia_iniziale_wh']
                    commessa['energia_finale_wh'] = energia_data['energia_finale_wh']
                    commessa['energia_consumata_wh'] = energia_data['energia_consumata_wh']
                else:
                    commessa['energia_calcolata_kwh'] = 0
                    commessa['progressivo_wh'] = commessa.get('potenza_consumata_tx', 0)
                    commessa['energia_iniziale_wh'] = commessa.get('energia_iniziale_wh', 0)
                    commessa['energia_finale_wh'] = commessa.get('energia_finale_wh', 0)
                    commessa['energia_consumata_wh'] = commessa.get('energia_consumata_wh', 0)
            else:
                commessa['energia_calcolata_kwh'] = 0
                commessa['progressivo_wh'] = commessa.get('potenza_consumata_tx', 0)
                commessa['energia_iniziale_wh'] = commessa.get('energia_iniziale_wh', 0)
                commessa['energia_finale_wh'] = commessa.get('energia_finale_wh', 0)
                commessa['energia_consumata_wh'] = commessa.get('energia_consumata_wh', 0)
        
        return {"commesse": commesse, "num_records": len(commesse)}
    except Exception as e:
        return {"error": f"Errore nel leggere i dati: {str(e)}"}

@app.route('/api/commesse/tutte')
def api_tutte():
    """Restituisce tutte le commesse salvate"""
    try:
        return {"commesse": db.leggi_tutti()}
    except Exception as e:
        return {"error": f"Errore nel leggere i dati: {str(e)}"}

@app.route('/api/report/giornaliero')
def api_report_giornaliero():
    """API per il report giornaliero"""
    try:
        data = request.query.data or datetime.date.today().isoformat()
        commesse = db.report_giornaliero(data)
        return {"commesse": commesse, "data": data}
    except Exception as e:
        return {"error": f"Errore nel report giornaliero: {str(e)}"}

@app.route('/api/report/mensile')
def api_report_mensile():
    """API per il report mensile"""
    try:
        anno = int(request.query.anno or datetime.date.today().year)
        mese = int(request.query.mese or datetime.date.today().month)
        commesse = db.report_mensile(anno, mese)
        statistiche = db.statistiche_mensili(anno, mese)
        
        nomi_mesi = [
            "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
            "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"
        ]
        nome_mese = nomi_mesi[mese - 1]
        
        return {
            "commesse": commesse, 
            "statistiche": statistiche,
            "anno": anno, 
            "mese": mese, 
            "nome_mese": nome_mese
        }
    except Exception as e:
        return {"error": f"Errore nel report mensile: {str(e)}"}

@app.route('/api/report/annuale')
def api_report_annuale():
    """API per il report annuale"""
    try:
        anno = int(request.query.anno or datetime.date.today().year)
        commesse = db.report_annuale(anno)
        statistiche = db.statistiche_annuali(anno)
        
        return {
            "commesse": commesse, 
            "statistiche": statistiche,
            "anno": anno
        }
    except Exception as e:
        return {"error": f"Errore nel report annuale: {str(e)}"}

@app.route('/api/export/csv')
def export_csv():
    """Esporta i dati in formato CSV"""
    try:
        commesse = db.leggi_tutti()
        if not commesse:
            return {"error": "Nessun dato da esportare"}
        
        # Crea il CSV
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        if commesse:
            writer.writerow(commesse[0].keys())
        
        # Dati
        for commessa in commesse:
            writer.writerow(commessa.values())
        
        csv_content = output.getvalue()
        output.close()
        
        from bottle import response
        response.content_type = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment; filename="telemetria.csv"'
        
        return csv_content
        
    except Exception as e:
        return {"error": f"Errore nell'esportazione: {str(e)}"}

@app.route('/api/export/pdf/giornaliero')
def export_pdf_giornaliero():
    """Esporta il report giornaliero in PDF"""
    try:
        data = request.query.data or datetime.date.today().isoformat()
        commesse = db.report_giornaliero(data)
        
        pdf_buffer = generate_pdf_report(
            commesse=commesse,
            titolo=f"Report Giornaliero - {data}",
            tipo_report="giornaliero"
        )
        
        from bottle import response
        response.content_type = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="report_giornaliero_{data}.pdf"'
        
        return pdf_buffer.getvalue()
        
    except Exception as e:
        return {"error": f"Errore nell'esportazione PDF: {str(e)}"}

@app.route('/api/export/pdf/mensile')
def export_pdf_mensile():
    """Esporta il report mensile in PDF"""
    try:
        anno = int(request.query.anno or datetime.date.today().year)
        mese = int(request.query.mese or datetime.date.today().month)
        commesse = db.report_mensile(anno, mese)
        statistiche = db.statistiche_mensili(anno, mese)
        
        nomi_mesi = [
            "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
            "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"
        ]
        nome_mese = nomi_mesi[mese - 1]
        
        pdf_buffer = generate_pdf_report(
            commesse=commesse,
            titolo=f"Report Mensile - {nome_mese} {anno}",
            tipo_report="mensile",
            statistiche=statistiche
        )
        
        from bottle import response
        response.content_type = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="report_mensile_{anno}_{mese:02d}.pdf"'
        
        return pdf_buffer.getvalue()
        
    except Exception as e:
        return {"error": f"Errore nell'esportazione PDF: {str(e)}"}

@app.route('/api/export/pdf/annuale')
def export_pdf_annuale():
    """Esporta il report annuale in PDF"""
    try:
        anno = int(request.query.anno or datetime.date.today().year)
        commesse = db.report_annuale(anno)
        statistiche = db.statistiche_annuali(anno)
        
        pdf_buffer = generate_pdf_report(
            commesse=commesse,
            titolo=f"Report Annuale - {anno}",
            tipo_report="annuale",
            statistiche=statistiche
        )
        
        from bottle import response
        response.content_type = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="report_annuale_{anno}.pdf"'
        
        return pdf_buffer.getvalue()
        
    except Exception as e:
        return {"error": f"Errore nell'esportazione PDF: {str(e)}"}

@app.route('/api/export/pdf/energia/mensile')
def export_pdf_energia_mensile():
    try:
        anno = int(request.query.anno or datetime.date.today().year)
        mese = int(request.query.mese or datetime.date.today().month)
        report = db.calcola_report_mensile(anno, mese)
        nomi_mesi = [
            "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
            "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"
        ]
        nome_mese = nomi_mesi[mese - 1]
        pdf_buffer = generate_energy_pdf_report(report, f"Report Energia Mensile - {nome_mese} {anno}")
        from bottle import response
        response.content_type = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="report_energia_mensile_{anno}_{mese:02d}.pdf"'
        return pdf_buffer.getvalue()
    except Exception as e:
        return {"error": f"Errore nell'esportazione PDF energia: {str(e)}"}

@app.route('/api/export/pdf/energia/annuale')
def export_pdf_energia_annuale():
    try:
        anno = int(request.query.anno or datetime.date.today().year)
        report = db.calcola_report_annuale(anno)
        pdf_buffer = generate_energy_pdf_report(report, f"Report Energia Annuale - {anno}")
        from bottle import response
        response.content_type = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="report_energia_annuale_{anno}.pdf"'
        return pdf_buffer.getvalue()
    except Exception as e:
        return {"error": f"Errore nell'esportazione PDF energia: {str(e)}"}

@app.route('/api/export/pdf/energia/settimanale')
def export_pdf_energia_settimanale():
    try:
        inizio = request.query.inizio or (datetime.date.today() - datetime.timedelta(days=6)).isoformat()
        fine = request.query.fine or datetime.date.today().isoformat()
        report = db.calcola_report_settimanale(inizio, fine)
        pdf_buffer = generate_energy_pdf_report(report, f"Report Energia Settimanale - {inizio} → {fine}")
        from bottle import response
        response.content_type = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename="report_energia_settimanale.pdf"'
        return pdf_buffer.getvalue()
    except Exception as e:
        return {"error": f"Errore nell'esportazione PDF energia: {str(e)}"}

@app.post('/api/commessa/imposta')
def imposta_commessa():
    data = request.json
    commessa_rx = data.get("commessa")
    cer_rx = data.get("cer")
    descrizione = data.get("descrizione", "")
    
    config = load_config()
    
    # Se non specificato, usa il CER di default
    if cer_rx is None:
        cer_rx = config.get("default_cer", 160214)

    if commessa_rx is None:
        return {"success": False, "error": "Campo 'commessa' obbligatorio"}

    try:
        
        # Registra il record nel database per tracciabilità
        try:
            # Crea un record di tracciabilità per l'impostazione manuale
            timestamp = datetime.datetime.now().isoformat()
            # Crea la descrizione combinando quella fornita dall'utente con il prefisso automatico
            descrizione_completa = f''
            if descrizione.strip():
                descrizione_completa += f'{descrizione.strip()}'
            
            record_data = {
                'timestamp': timestamp,
                'Commessa RX': commessa_rx,
                'Codice CER RX': cer_rx,
                'Codice CER TX': 0,
                'Commessa TX': 0,
                'Ore totali commessa TX': 0,
                'Minuti totali commessa TX': 0,
                'Ore lavorate commessa TX': 0,
                'Minuti lavorati commessa TX': 0,
                'Potenza consumata TX': 0,
                'Descrizione commessa': descrizione_completa,
                'stato_lavorazione': 'non_iniziata'
            }
            
            db.insert_record(record_data)
            print(f"📝 Record di tracciabilità creato per commessa {commessa_rx} impostata manualmente")
            
        except Exception as db_error:
            print(f"⚠️ Errore nella registrazione del record di tracciabilità: {db_error}")
            # Non blocchiamo l'operazione se c'è un errore nel database

#        # Invia i dati al PLC
#        if poller and poller_running:
#            success = poller.write_tags(commessa_rx, cer_rx)
#            if not success:
#                return {"success": False, "error": "Errore nell'invio al PLC"}
#        else:
#            return {"success": False, "error": "Provider di dati non disponibile"}
        
        return {"success": True, "message": f"Commessa {commessa_rx} impostata con successo"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.route('/api/commessa/ultima')
def ultima_commessa():
    """Restituisce l'ultima commessa utilizzata"""
    try:
        # Ottieni l'ultimo record dal database
        ultimi = db.leggi_ultimi(1)
        if ultimi:
            ultima_commessa = ultimi[0].get('commessa_tx', 0)
            return {"ultima_commessa": ultima_commessa}
        else:
            return {"ultima_commessa": 0}
    except Exception as e:
        return {"error": f"Errore nel leggere l'ultima commessa: {str(e)}"}

@app.post('/api/commessa/descrizione')
def aggiorna_descrizione_commessa():
    """Aggiorna la descrizione di una commessa specifica"""
    data = request.json
    commessa_tx = data.get("commessa")
    descrizione = data.get("descrizione", "")
    
    if commessa_tx is None:
        return {"success": False, "error": "Campo 'commessa' obbligatorio"}
    
    try:
        success = db.aggiorna_descrizione_commessa(commessa_tx, descrizione)
        if success:
            return {"success": True, "message": f"Descrizione aggiornata per commessa {commessa_tx}"}
        else:
            return {"success": False, "error": f"Commessa {commessa_tx} non trovata"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.route('/api/commessa/energia/<commessa_tx>')
def calcola_energia_commessa(commessa_tx):
    """Calcola l'energia consumata per una commessa specifica"""
    try:
        commessa_tx = int(commessa_tx)
        energia_data = db.calcola_energia_commessa(commessa_tx)
        
        if energia_data is None:
            return {"success": False, "error": "Commessa non trovata"}
        
        return {
            "success": True,
            "commessa_tx": commessa_tx,
            "energia_consumata_wh": energia_data['energia_consumata_wh'],
            "energia_consumata_kwh": round(energia_data['energia_consumata_kwh'], 3),
            "energia_iniziale_wh": energia_data['energia_iniziale_wh'],
            "energia_finale_wh": energia_data['energia_finale_wh'],
            "progressivo_finale": energia_data['progressivo_finale'],
            "timestamp": energia_data['timestamp'],
            "descrizione": energia_data['descrizione'],
            "stato_lavorazione": energia_data['stato_lavorazione']
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.route('/api/report/giornaliero/<data>')
def report_giornaliero(data):
    """Genera il report energetico giornaliero"""
    try:
        # Accetta formati multipli e normalizza a YYYY-MM-DD
        from datetime import datetime
        data = data.strip()
        formati = ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d']
        parsed = None
        for fmt in formati:
            try:
                parsed = datetime.strptime(data, fmt)
                break
            except ValueError:
                continue
        if not parsed:
            return {"success": False, "error": "Formato data non valido. Usa YYYY-MM-DD"}
        data_norm = parsed.strftime('%Y-%m-%d')

        report = db.calcola_report_giornaliero(data_norm)
        
        return {
            "success": True,
            "report": report
        }
        
    except ValueError:
        return {"success": False, "error": "Formato data non valido. Usa YYYY-MM-DD"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.route('/api/report/oggi')
def report_oggi():
    """Genera il report energetico per oggi"""
    try:
        from datetime import datetime, date
        oggi = date.today().strftime('%Y-%m-%d')
        
        report = db.calcola_report_giornaliero(oggi)
        
        return {
            "success": True,
            "report": report
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.route('/api/commesse/energia/tutte')
def calcola_energia_tutte_commesse():
    """Calcola l'energia consumata per tutte le commesse"""
    try:
        commesse_energia = db.calcola_energia_tutte_commesse()
        
        # Calcola statistiche
        totale_energia_wh = sum(c['energia_consumata_wh'] for c in commesse_energia)
        totale_energia_kwh = totale_energia_wh / RAW_TO_KWH
        energia_media_kwh = totale_energia_kwh / len(commesse_energia) if commesse_energia else 0
        
        return {
            "success": True,
            "commesse": commesse_energia,
            "statistiche": {
                "totale_commesse": len(commesse_energia),
                "energia_totale_wh": totale_energia_wh,
                "energia_totale_kwh": round(totale_energia_kwh, 3),
                "energia_media_kwh": round(energia_media_kwh, 3)
            }
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.route('/api/energia/statistiche')
def api_statistiche_energia():
    """API per le statistiche dell'energia di tutte le commesse"""
    try:
        # Usa tutti i record per le statistiche
        commesse = db.leggi_ultimi(1000)  # Numero molto alto per includere tutti i record
        
        if not commesse:
            return {
                "success": True,
                "statistiche": {
                    "totale_commesse": 0,
                    "energia_totale_kwh": 0,
                    "energia_media_kwh": 0,
                    "progressivo_massimo_wh": 0
                }
            }
        
        energia_totale = 0
        progressivo_massimo = 0
        
        for commessa in commesse:
            commessa_tx = commessa.get('commessa_tx')
            if commessa_tx:
                energia_data = db.calcola_energia_commessa(commessa_tx)
                if energia_data:
                    energia_totale += energia_data['energia_consumata_kwh']
                    progressivo_massimo = max(progressivo_massimo, energia_data['progressivo_finale'])
                else:
                    progressivo_massimo = max(progressivo_massimo, commessa.get('potenza_consumata_tx', 0))
            else:
                progressivo_massimo = max(progressivo_massimo, commessa.get('potenza_consumata_tx', 0))
        
        energia_media = energia_totale / len(commesse) if commesse else 0
        
        return {
            "success": True,
            "statistiche": {
                "totale_commesse": len(commesse),
                "energia_totale_kwh": round(energia_totale, 3),
                "energia_media_kwh": round(energia_media, 3),
                "progressivo_massimo_wh": progressivo_massimo
            }
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.route('/api/energia/report/settimanale')
def api_report_energia_settimanale():
    """API report energetico settimanale: ?inizio=YYYY-MM-DD&fine=YYYY-MM-DD"""
    try:
        inizio = request.query.inizio
        fine = request.query.fine
        if not inizio or not fine:
            return {"success": False, "error": "Parametri 'inizio' e 'fine' obbligatori (YYYY-MM-DD)"}
        report = db.calcola_report_settimanale(inizio, fine)
        return {"success": True, "report": report}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.route('/api/energia/report/mensile')
def api_report_energia_mensile():
    """API report energetico mensile: ?anno=YYYY&mese=MM"""
    try:
        anno = int(request.query.anno or datetime.date.today().year)
        mese = int(request.query.mese or datetime.date.today().month)
        report = db.calcola_report_mensile(anno, mese)
        return {"success": True, "report": report, "anno": anno, "mese": mese}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.route('/api/energia/report/annuale')
def api_report_energia_annuale():
    """API report energetico annuale: ?anno=YYYY"""
    try:
        anno = int(request.query.anno or datetime.date.today().year)
        report = db.calcola_report_annuale(anno)
        return {"success": True, "report": report, "anno": anno}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.route('/report/energia/mensile')
def report_energia_mensile():
    """Pagina HTML report energetico mensile con grafici"""
    anno = int(request.query.anno or datetime.date.today().year)
    mese = int(request.query.mese or datetime.date.today().month)
    report = db.calcola_report_mensile(anno, mese)
    nomi_mesi = [
        "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
        "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"
    ]
    nome_mese = nomi_mesi[mese - 1]
    return template("report_energia", report=report, titolo=f"Energia {nome_mese} {anno}",
                    livello="mensile", anno=anno, mese=mese, nome_mese=nome_mese)

@app.route('/report/energia/annuale')
def report_energia_annuale():
    """Pagina HTML report energetico annuale con grafici"""
    anno = int(request.query.anno or datetime.date.today().year)
    report = db.calcola_report_annuale(anno)
    return template("report_energia", report=report, titolo=f"Energia Annuale {anno}",
                    livello="annuale", anno=anno)

@app.route('/report/energia/settimanale')
def report_energia_settimanale():
    """Pagina HTML report energetico settimanale con grafici: ?inizio=YYYY-MM-DD&fine=YYYY-MM-DD"""
    inizio = request.query.inizio or (datetime.date.today() - datetime.timedelta(days=6)).isoformat()
    fine = request.query.fine or datetime.date.today().isoformat()
    report = db.calcola_report_settimanale(inizio, fine)
    return template("report_energia", report=report, titolo=f"Energia Settimanale {inizio} → {fine}",
                    livello="settimanale", inizio=inizio, fine=fine)

@app.route('/api/status')
def api_status():
    """Endpoint per verificare lo stato del sistema"""
    config = load_config()
    return {
        "poller_running": poller_running,
        "poller_available": poller is not None,
        "mode": config.get("mode", "opcua"),
        "database_available": True,  # Il database è sempre disponibile
        "config": {
            "opcua_server_url": config.get("opcua_server_url"),
            "default_cer": config.get("default_cer", 160214),
            "auto_increment_commessa": config.get("auto_increment_commessa", True),
            "auto_send_to_plc": config.get("auto_send_to_plc", True)
        }
    }

@app.route('/api/config')
def api_config():
    """Endpoint per ottenere la configurazione"""
    return load_config()

@app.post('/api/config/update')
def api_config_update():
    """Endpoint per aggiornare la configurazione"""
    try:
        data = request.json
        if not data:
            return {"success": False, "error": "Dati mancanti"}
        
        # Validazione password (da file)
        password = data.get("password")
        admin_password = "admin123"  # Default
        
        # Prova a leggere da file
        try:
            with open("admin_password.txt", "r") as f:
                admin_password = f.read().strip()
        except:
            pass  # Usa il default se il file non esiste
        
        if password != admin_password:
            return {"success": False, "error": "Password non valida"}
        
        # Rimuovi la password dai dati da salvare
        config_data = {k: v for k, v in data.items() if k != "password"}
        
        success = save_config(config_data)
        return {"success": success, "message": "Configurazione aggiornata" if success else "Errore nel salvataggio"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post('/api/config/reset')
def api_config_reset():
    """Reset della configurazione ai valori di default"""
    try:
        data = request.json
        password = data.get("password")
        admin_password = "admin123"  # Default
        
        # Prova a leggere da file
        try:
            with open("admin_password.txt", "r") as f:
                admin_password = f.read().strip()
        except:
            pass  # Usa il default se il file non esiste
        
        if password != admin_password:
            return {"success": False, "error": "Password non valida"}
        
        from dynamic_config import DEFAULT_CONFIG
        success = save_config(DEFAULT_CONFIG)
        return {"success": success, "message": "Configurazione resettata" if success else "Errore nel reset"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post('/api/poller/restart')
def restart_poller():
    """Riavvia il poller"""
    global poller_running
    
    # Ferma il poller esistente
    stop_poller()
    
    # Determina la modalità
    mode = get_mode_from_env()
    if len(sys.argv) > 1:
        mode = sys.argv[1]
    
    # Riavvia il poller
    success = start_poller_in_background(mode)
    
    return {
        "success": success,
        "message": "Poller riavviato" if success else "Errore nel riavvio del poller"
    }

@app.post('/api/poller/stop')
def stop_poller_api():
    """Ferma il poller"""
    stop_poller()
    return {"success": True, "message": "Poller fermato"}

@app.post('/api/poller/start')
def start_poller_api():
    """Avvia il poller"""
    mode = get_mode_from_env()
    if len(sys.argv) > 1:
        mode = sys.argv[1]
    
    success = start_poller_in_background(mode)
    return {
        "success": success,
        "message": "Poller avviato" if success else "Errore nell'avvio del poller"
    }

# TODO: api/report_mensile, api/report_annuale ...

def on_change(new_values, old_values):
    """
    Gestisce i cambiamenti di stato delle commesse con logica semplificata:
    
    STATI:
    - preparazione: commessa impostata manualmente
    - in_lavorazione: lavorazione iniziata, energia iniziale registrata
    - completata: lavorazione terminata, energia finale calcolata
    """
    config = load_config()
    crx = new_values["Commessa RX"]
    ctx = new_values["Commessa TX"]
    energia_attuale = new_values.get("Potenza consumata TX", 0)
    
    print(f'{new_values["timestamp"]} RX: {crx} TX: {ctx}')
    
    # CASO 1: LAVORAZIONE INIZIATA (crx != 0, ctx == 0)
    if crx != 0 and ctx == 0:
        print(f"🔄 Lavorazione iniziata per commessa {crx}")
        
        # Se non esiste un record, crealo automaticamente in stato 'preparazione'
        if not db.commessa_esiste(crx):
            try:
                timestamp = datetime.datetime.now().isoformat()
                record_data = {
                    'timestamp': timestamp,
                    'Commessa RX': crx,
                    'Codice CER RX': config.get("default_cer", 160214),
                    'Codice CER TX': config.get("default_cer", 160214),
                    'Commessa TX': crx,
                    'Ore totali commessa TX': 0,
                    'Minuti totali commessa TX': 0,
                    'Ore lavorate commessa TX': 0,
                    'Minuti lavorati commessa TX': 0,
                    'Potenza consumata TX': energia_attuale or 0,
                    'Descrizione commessa': f"Creato automaticamente all'avvio della lavorazione (commessa {crx})",
                    'stato_lavorazione': 'preparazione'
                }
                db.insert_record(record_data)
                print(f"📝 Record creato automaticamente per commessa {crx} (preparazione)")
            except Exception as e:
                print(f"❌ Errore nella creazione automatica del record: {e}")
        
        # Aggiorna il record esistente con energia iniziale e stato
        try:
            db.aggiorna_energia_iniziale(crx, energia_attuale)
            print(f"⚡ Energia iniziale registrata: {energia_attuale} Wh per commessa {crx}")
        except Exception as e:
            print(f"❌ Errore nella registrazione energia iniziale: {e}")
    
    # CASO 2: FASE REGISTRAZIONE (crx == ctx != 0)
    elif crx == ctx and crx != 0:
        print(f"📝 Fase registrazione per commessa {crx}")
        
        # Aggiorna solo i dati operativi, mantieni energia iniziale e descrizione
        try:
            db.aggiorna_dati_operativi(crx, new_values)
            print(f"📊 Dati operativi aggiornati per commessa {crx}")
        except Exception as e:
            print(f"❌ Errore nell'aggiornamento dati operativi: {e}")
    
    ## CASO 2bis: FASE REGISTRAZIONE (crx != ctx != 0)
    #elif crx != ctx and crx != 0:
    #    print(f"📝 Fase registrazione per commessa {ctx}")
    #    # Se non esiste un record, crealo automaticamente in stato 'preparazione'
    #    if not db.commessa_esiste(ctx):
    #        try:
    #            timestamp = datetime.datetime.now().isoformat()
    #            record_data = {
    #                'timestamp': timestamp,
    #                'Commessa RX': ctx,
    #                'Codice CER RX': config.get("default_cer", 160214),
    #                'Codice CER TX': config.get("default_cer", 160214),
    #                'Commessa TX': ctx,
    #                'Ore totali commessa TX': 0,
    #                 'Minuti totali commessa TX': 0,
    #                'Ore lavorate commessa TX': 0,
    #                'Minuti lavorati commessa TX': 0,
    #                'Potenza consumata TX': energia_attuale or 0,
    #                'Descrizione commessa': f"Creato automaticamente all'avvio della lavorazione (commessa {ctx})",
    #                'stato_lavorazione': 'preparazione'
   #             }
   #             db.insert_record(record_data)
   #             print(f"📝 Record creato automaticamente per commessa {ctx} (preparazione)")
   #         except Exception as e:
   #             print(f"❌ Errore nella creazione automatica del record: {e}")
        
        # Aggiorna solo i dati operativi, mantieni energia iniziale e descrizione
   #     try:
   #         db.aggiorna_dati_operativi(ctx, new_values)
   #         print(f"📊 Dati operativi aggiornati per commessa {crx}")
   #     except Exception as e:
   #         print(f"❌ Errore nell'aggiornamento dati operativi: {e}")
    
    # CASO 3: LAVORAZIONE COMPLETATA (crx == 0, ctx != 0)
    elif crx == 0 and ctx != 0:
        print(f"✅ Lavorazione completata per commessa {ctx}")
        
        try:
            energia_data = db.aggiorna_energia_finale(ctx, energia_attuale)
            if energia_data is not None:
                print(f"⚡ Energia consumata: {energia_data['energia_consumata_wh']} Wh")
                
                # Auto-increment, invio al PLC e creazione record "preparazione" per la nuova commessa
                try:
                    ultimi = db.leggi_ultimi(1)
                    ultima_commessa = ultimi[0].get('commessa_tx', 0) if ultimi else ctx
                    nuova_commessa = max(ultima_commessa, ctx) + 1
                    default_cer = config.get("default_cer", 160214)

                    print(f"Auto-preparazione nuova commessa: {nuova_commessa}")

                    sent=None
                    # Tenta invio automatico, se abilitato
                    if config.get("auto_send_to_plc", True) and poller and poller_running:
                        try:
                            sent = poller.write_tags(nuova_commessa, default_cer)
                            if sent:
                                print(f"✅ Commessa {nuova_commessa} inviata automaticamente al PLC")
                            else:
                                print(f"⚠️ Invio automatico al PLC non riuscito per commessa {nuova_commessa}")
                        except Exception as e:
                            print(f"⚠️ Errore invio automatico al PLC: {e}")

                    # Crea comunque il record in stato "preparazione" anche se l'invio al PLC manca
                    if not db.commessa_esiste(nuova_commessa) and sent:
                        try:
                            timestamp = datetime.datetime.now().isoformat()
                            nuovo_record = {
                                'timestamp': timestamp,
                                'Commessa RX': nuova_commessa,
                                'Codice CER RX': default_cer,
                                'Codice CER TX': default_cer,
                                'Commessa TX': nuova_commessa,
                                'Ore totali commessa TX': 0,
                                'Minuti totali commessa TX': 0,
                                'Ore lavorate commessa TX': 0,
                                'Minuti lavorati commessa TX': 0,
                                'Potenza consumata TX': energia_attuale or 0,
                                'Descrizione commessa': f"Creato automaticamente alla chiusura della commessa {ctx}",
                                'stato_lavorazione': 'preparazione'
                            }
                            db.insert_record(nuovo_record)
                            print(f"📝 Record creato automaticamente per nuova commessa {nuova_commessa} (preparazione)")
                        except Exception as e:
                            print(f"❌ Errore creazione record nuova commessa {nuova_commessa}: {e}")
                except Exception as e:
                    print(f"Errore nell'auto-preparazione nuova commessa: {e}")
            else:
                print(f"⚠️ Commessa {ctx} non trovata in lavorazione")
        except Exception as e:
            print(f"❌ Errore nella registrazione energia finale: {e}")
    
    # CASO 4: ALTRI STATI (preparazione, attesa, ecc.)
    else:
        print(f"⏳ Stato: In preparazione")

def run_server_only():
    """Avvia solo il server web senza provider di dati"""
    print("Avvio server web in modalità standalone (senza provider di dati)")
    run(app, host=WEB_HOST, port=WEB_PORT, debug=WEB_DEBUG, reloader=False)

if __name__ == '__main__':
    # Determina la modalità: argomento a riga di comando, oppure env OPC_LOGGER_MODE, oppure default standalone
    mode = None
    if len(sys.argv) > 1:
        mode = sys.argv[1]
    if mode is None:
        mode = get_mode_from_env()
    print(f"Avvio server in modalità: {mode}")
    
    # Prova ad avviare il poller
    poller_started = start_poller_in_background(mode)
    
    if not poller_started:
        print("Impossibile avviare il provider di dati, continuo con il server web...")
    
    try:
        # Avvia sempre il server web, indipendentemente dal poller
        run(app, host=WEB_HOST, port=WEB_PORT, debug=WEB_DEBUG, reloader=False)
    except KeyboardInterrupt:
        print("Interrotto")
    except Exception as e:
        print(f"Errore nell'avvio del server web: {e}")
    finally:
        stop_poller()



