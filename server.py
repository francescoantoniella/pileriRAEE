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

def create_data_provider(mode=None):
    """Crea il provider di dati appropriato"""
    if mode is None:
        mode = get_mode_from_env()
    
    if mode == "opcua":
        print("Tentativo di connessione OPC UA...")
        return OpcuaReader(
            server_url=OPCUA_SERVER_URL,
            tag_names=TAG_LIST,
            tag_check=TAG_CHECK,
            namespace_index=OPCUA_NAMESPACE_INDEX,
            tag_prefix=OPCUA_TAG_PREFIX,
            on_change_callback=on_change,
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
    
    # Usa i valori di default se non specificati
    if max_retries is None:
        max_retries = POLLER_MAX_RETRIES
    if retry_delay is None:
        retry_delay = POLLER_RETRY_DELAY
    
    def poller_worker():
        global poller_running
        retry_count = 0
        
        while poller_running and retry_count < max_retries:
            try:
                poller.connect()
                poller.start_polling()
                poller_running = True
                print(f"Provider di dati avviato (tentativo {retry_count + 1})")
                
                # Mantieni il thread attivo
                while poller_running:
                    time.sleep(1)
                    
            except Exception as e:
                print(f"Errore nel provider di dati (tentativo {retry_count + 1}): {e}")
                poller_running = False
                retry_count += 1
                
                if retry_count < max_retries:
                    print(f"Riprovo tra {retry_delay} secondi...")
                    time.sleep(retry_delay)
                else:
                    print("Numero massimo di tentativi raggiunto, poller fermato")
                    break
    
    try:
        poller = create_data_provider(mode)
        poller_thread = threading.Thread(target=poller_worker, daemon=True)
        poller_thread.start()
        return True
    except Exception as e:
        print(f"Errore nell'avvio del provider di dati: {e}")
        return False

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
        headers = ['Timestamp', 'Commessa', 'CER', 'Ore Totali', 'Minuti Totali', 
                  'Ore Lavorate', 'Minuti Lavorati', 'Energia (kWh)']
        
        # Dati
        data = [headers]
        for riga in commesse:
            data.append([
                riga['timestamp'],
                str(riga['commessa_tx']),
                str(riga['codice_cer_tx']),
                str(riga['ore_totali_commessa_tx']),
                str(riga['minuti_totali_commessa_tx']),
                str(riga['ore_lavorate_commessa_tx']),
                str(riga['minuti_lavorati_commessa_tx']),
                str(riga['potenza_consumata_tx'])
            ])
        
        # Crea tabella
        table = Table(data, colWidths=[1.2*inch, 0.8*inch, 0.8*inch, 0.8*inch, 
                                      0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch])
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

@app.route('/')
def home():
    # Permette di specificare il numero di record tramite parametro URL
    n = request.query.n
    if n is not None:
        try:
            n = int(n)
            # Limita il numero massimo per evitare sovraccarichi
            if n > 100:
                n = 100
            elif n < 1:
                n = 10
        except ValueError:
            n = 10
    else:
        n = 10
    
    recenti = db.leggi_ultimi(n)
    return template("index", commesse=recenti, num_records=n)

@app.route('/report/giornaliero')
def report_giornaliero():
    data = request.query.data or datetime.date.today().isoformat()
    commesse = db.report_giornaliero(data)
    return template("report", commesse=commesse, titolo=f"Report {data}")

@app.route('/report/mensile')
def report_mensile():
    anno = int(request.query.anno or datetime.date.today().year)
    mese = int(request.query.mese or datetime.date.today().month)
    commesse = db.report_mensile(anno, mese)
    statistiche = db.statistiche_mensili(anno, mese)
    
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
    """API per le commesse recenti con controllo del numero di record"""
    n = request.query.n
    if n is not None:
        try:
            n = int(n)
            # Limita il numero massimo per evitare sovraccarichi
            if n > 100:
                n = 100
            elif n < 1:
                n = 5
        except ValueError:
            n = 5
    else:
        n = 5
    
    try:
        return {"commesse": db.leggi_ultimi(n), "num_records": n}
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

@app.post('/api/commessa/imposta')
def imposta_commessa():
    data = request.json
    commessa_rx = data.get("commessa")
    cer_rx = data.get("cer")

    if commessa_rx is None or cer_rx is None:
        return {"success": False, "error": "Campi 'commessa' e 'cer' obbligatori"}

    try:
        if poller and poller_running:
            success = poller.write_tags(commessa_rx, cer_rx)
            return {"success": success}
        else:
            return {"success": False, "error": "Provider di dati non disponibile"}
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

@app.route('/api/status')
def api_status():
    """Endpoint per verificare lo stato del sistema"""
    return {
        "poller_running": poller_running,
        "poller_available": poller is not None,
        "mode": get_mode_from_env(),
        "database_available": True  # Il database è sempre disponibile
    }

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
    status = ""
    crx=new_values["Commessa RX"]
    ctx=new_values["Commessa TX"]
    if crx==ctx:
        status = "In registrazione"
    elif crx!=0 and ctx==0:
        status = "In lavorazione"
    elif crx==0 and ctx!=0:
        status = f"Dati registrati\n{new_values}\n"
        db.insert_record(new_values)
    else:
        status = "In preparazione"
    print(f'{new_values["timestamp"]} RX: {crx}  TX: {ctx} Stato: {status}')

def run_server_only():
    """Avvia solo il server web senza provider di dati"""
    print("Avvio server web in modalità standalone (senza provider di dati)")
    run(app, host=WEB_HOST, port=WEB_PORT, debug=WEB_DEBUG, reloader=False)

if __name__ == '__main__':
    # Determina la modalità di esecuzione
    mode = None
    if len(sys.argv) > 1:
        mode = sys.argv[1]
    
    print(f"Avvio server in modalità: {mode or get_mode_from_env()}")
    
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



