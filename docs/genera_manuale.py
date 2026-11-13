"""Genera docs/Manuale_sistema_RAEE.pdf. Uso: python docs/genera_manuale.py"""
import os
from datetime import date

from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table,
                                TableStyle, PageBreak, KeepTogether)
from reportlab.platypus.tableofcontents import TableOfContents

QUI = os.path.dirname(os.path.abspath(__file__))
USCITA = os.path.join(QUI, "Manuale_sistema_RAEE.pdf")
VERSIONE = date.today().strftime("%d/%m/%Y")

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
pdfmetrics.registerFont(TTFont("Sans", f"{FONT_DIR}/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("Sans-B", f"{FONT_DIR}/DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Sans-I", f"{FONT_DIR}/DejaVuSans-Oblique.ttf"))
pdfmetrics.registerFont(TTFont("Mono", f"{FONT_DIR}/DejaVuSansMono.ttf"))
pdfmetrics.registerFontFamily("Sans", normal="Sans", bold="Sans-B", italic="Sans-I", boldItalic="Sans-B")

BLU = colors.HexColor("#1f4e79")
BLU_CHIARO = colors.HexColor("#dbe7f3")
GRIGIO = colors.HexColor("#f2f2f2")
ARANCIO = colors.HexColor("#fff4e0")

S = {
    "titolo": ParagraphStyle("titolo", fontName="Sans-B", fontSize=26, leading=32, textColor=BLU),
    "sottotitolo": ParagraphStyle("sottotitolo", fontName="Sans", fontSize=14, leading=20, textColor=colors.grey),
    "h1": ParagraphStyle("h1", fontName="Sans-B", fontSize=16, leading=22, textColor=BLU, spaceBefore=6, spaceAfter=8),
    "h2": ParagraphStyle("h2", fontName="Sans-B", fontSize=12, leading=16, textColor=BLU, spaceBefore=10, spaceAfter=4),
    "p": ParagraphStyle("p", fontName="Sans", fontSize=9.5, leading=14, spaceAfter=6, alignment=TA_LEFT),
    "li": ParagraphStyle("li", fontName="Sans", fontSize=9.5, leading=14, leftIndent=14, bulletIndent=4, spaceAfter=2),
    "cella": ParagraphStyle("cella", fontName="Sans", fontSize=8.5, leading=11),
    "cella_b": ParagraphStyle("cella_b", fontName="Sans-B", fontSize=8.5, leading=11, textColor=colors.white),
    "codice": ParagraphStyle("codice", fontName="Mono", fontSize=8, leading=11, backColor=GRIGIO,
                             borderPadding=5, leftIndent=5, rightIndent=5, spaceBefore=4, spaceAfter=8),
    "nota": ParagraphStyle("nota", fontName="Sans", fontSize=9, leading=13, backColor=ARANCIO,
                           borderPadding=6, leftIndent=6, rightIndent=6, spaceBefore=4, spaceAfter=10),
    "toc1": ParagraphStyle("toc1", fontName="Sans", fontSize=10.5, leading=18, leftIndent=10),
}


def P(t, st="p"):
    return Paragraph(t, S[st])


def elenco(*voci):
    return [Paragraph(v, S["li"], bulletText="•") for v in voci]


def codice(t):
    return Paragraph(t.strip().replace("\n", "<br/>").replace("  ", "&nbsp;&nbsp;"), S["codice"])


def nota(t):
    return Paragraph(t, S["nota"])


def tabella(righe, larghezze):
    dati = [[Paragraph(str(c), S["cella_b"]) for c in righe[0]]]
    dati += [[Paragraph(str(c), S["cella"]) for c in r] for r in righe[1:]]
    t = Table(dati, colWidths=[w * cm for w in larghezze], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLU),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIGIO]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#bfbfbf")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


def schema_architettura():
    d = Drawing(17 * cm, 6.2 * cm)

    def blocco(x, y, w, h, titolo, righe, colore=BLU_CHIARO):
        d.add(Rect(x, y, w, h, fillColor=colore, strokeColor=BLU, strokeWidth=1, rx=6, ry=6))
        d.add(String(x + w / 2, y + h - 16, titolo, fontName="Sans-B", fontSize=10, fillColor=BLU, textAnchor="middle"))
        for i, r in enumerate(righe):
            d.add(String(x + w / 2, y + h - 32 - i * 12, r, fontName="Sans", fontSize=7.5, textAnchor="middle"))

    def freccia(x1, y, x2, testo_su, testo_giu):
        d.add(Line(x1, y, x2 - 6, y, strokeColor=BLU, strokeWidth=1.3))
        d.add(Polygon([x2, y, x2 - 7, y + 4, x2 - 7, y - 4], fillColor=BLU, strokeColor=BLU))
        d.add(Line(x2, y - 14, x1 + 6, y - 14, strokeColor=BLU, strokeWidth=1.3))
        d.add(Polygon([x1, y - 14, x1 + 7, y - 10, x1 + 7, y - 18], fillColor=BLU, strokeColor=BLU))
        d.add(String((x1 + x2) / 2, y + 6, testo_su, fontName="Sans", fontSize=7, textAnchor="middle"))
        d.add(String((x1 + x2) / 2, y - 26, testo_giu, fontName="Sans", fontSize=7, textAnchor="middle"))

    blocco(0, 1.2 * cm, 4.2 * cm, 3.6 * cm, "PLC macchina", ["Siemens S7-1200/1500", "server OPC UA", "192.168.1.2:4840", "contatore energia"])
    blocco(6.4 * cm, 0.2 * cm, 4.6 * cm, 5.6 * cm, "Raspberry Pi", ["“impiantoraee”", "192.168.1.9 (LAN)", "servizio opc_logger", "server.py (Bottle)", "DB SQLite + log CSV", "backup giornaliero"])
    blocco(13.2 * cm, 1.2 * cm, 3.8 * cm, 3.6 * cm, "Browser", ["PC / tablet in LAN", "http://192.168.1.9", "dashboard e report", "PDF e CSV"])
    freccia(4.2 * cm, 3.3 * cm, 6.4 * cm, "letture ogni 2 s", "commessa + CER")
    freccia(11 * cm, 3.3 * cm, 13.2 * cm, "pagine, dati", "comandi")
    return d


class Manuale(BaseDocTemplate):
    def __init__(self, path):
        super().__init__(path, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm,
                         bottomMargin=2 * cm, title="Manuale del sistema di monitoraggio RAEE",
                         author="Pileri - impianto RAEE")
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="f")
        self.addPageTemplates([PageTemplate("normale", [frame], onPage=self._piede)])

    def _piede(self, c, doc):
        if doc.page == 1:
            return
        c.saveState()
        c.setFont("Sans", 7.5)
        c.setFillColor(colors.grey)
        c.drawString(2 * cm, 1.2 * cm, "Sistema di monitoraggio RAEE · manuale")
        c.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"pagina {doc.page}")
        c.setStrokeColor(BLU_CHIARO)
        c.line(2 * cm, 1.5 * cm, A4[0] - 2 * cm, 1.5 * cm)
        c.restoreState()

    def afterFlowable(self, f):
        if isinstance(f, Paragraph) and f.style.name == "h1":
            self.notify("TOCEntry", (0, f.getPlainText(), self.page))


def H1(t):
    return Paragraph(t, S["h1"])


def H2(t):
    return Paragraph(t, S["h2"])


def contenuto():
    st = []
    # --- Copertina
    st += [Spacer(1, 5 * cm), P("Sistema di monitoraggio<br/>impianto RAEE", "titolo"), Spacer(1, 0.6 * cm),
           P("Manuale d'uso e di manutenzione", "sottotitolo"), Spacer(1, 0.3 * cm),
           P(f"Versione del {VERSIONE}", "sottotitolo"), Spacer(1, 2.5 * cm),
           P("Il manuale descrive il logger che registra le commesse e l'energia della macchina dell'impianto RAEE: "
             "a cosa serve, come si usa ogni giorno, come leggere i report e come si mantiene il sistema."),
           PageBreak()]
    toc = TableOfContents()
    toc.levelStyles = [S["toc1"]]
    st += [P("Indice", "h2"), toc, PageBreak()]

    # --- 1
    st += [H1("1. A cosa serve"),
           P("Il sistema collega il PLC della macchina a un piccolo computer (Raspberry Pi) che:"),
           *elenco("legge dal PLC, ogni 2 secondi, il numero di commessa, il codice CER, le ore della commessa e il contatore dell'energia;",
                   "registra in un database ogni commessa con l'energia consumata dall'inizio alla fine della lavorazione;",
                   "invia al PLC la commessa successiva (numerazione automatica) o quella impostata a mano dalla dashboard;",
                   "mostra una dashboard web e produce report giornalieri, settimanali, mensili e annuali, anche in PDF e CSV."),
           P("Serve quindi a sapere, per ogni commessa RAEE, quanta energia ha consumato la macchina e quanto tempo è "
             "stata in lavorazione, e a ricostruire i consumi di un periodo."),
           ]

    # --- 2
    st += [H1("2. Come è fatto"), schema_architettura(), Spacer(1, 0.3 * cm),
           tabella([
               ["Parte", "Cosa fa", "Dove"],
               ["PLC", "Gestisce la macchina. Espone i tag della commessa e il contatore dell'energia con un server OPC UA.", "192.168.1.2, porta 4840"],
               ["Raspberry Pi “impiantoraee”", "Esegue il servizio <b>opc_logger</b>: legge il PLC, scrive il database, serve la dashboard.", "LAN 192.168.1.9; da remoto 10.8.0.5 (VPN WireGuard)"],
               ["server.py", "Server web (Bottle) e logica delle commesse.", "/home/pi/opc_logger"],
               ["opcua_reader.py", "Dialoga con il PLC: letture e scritture dei tag.", "idem"],
               ["db.py", "Database SQLite delle commesse e calcolo dei report energetici.", "telemetria_ricostruita.db"],
               ["Log CSV", "Una riga ogni lettura dal PLC: è la registrazione grezza, utile per ricostruire i dati.", "data_AAAA-MM-GG.log(.gz)"],
           ], [3.6, 8.4, 5]),
           Spacer(1, 0.2 * cm),
           P("Il codice sorgente è nel repository Git <b>pileriRAEE</b> (ramo <b>dev</b>); la copia di lavoro sul PC è in "
             "<font name='Mono'>~/001-Apps/Pileri/raee/opc_logger</font>."),
           ]

    # --- 3
    st += [H1("3. Uso quotidiano"),
           H2("Aprire la dashboard"),
           P("Da un PC o tablet collegato alla rete dello stabilimento aprire il browser all'indirizzo "
             "<b>http://192.168.1.9</b>. La pagina si aggiorna da sola e contiene queste sezioni:"),
           tabella([
               ["Sezione", "A cosa serve"],
               ["Status Sistema", "Indica se il servizio di lettura è attivo e in che modalità. Non dice se il PLC risponde: se i Dati Recenti non cambiano durante una lavorazione, guardare il log del servizio (sezione 7)."],
               ["Imposta Commessa", "Invia al PLC un numero di commessa e un codice CER (vedi sotto)."],
               ["Dati Recenti", "Ultime commesse registrate, con stato, ore ed energia in kWh."],
               ["Statistiche Stati Commesse", "Quante commesse ci sono in preparazione, in lavorazione e completate."],
               ["Statistiche Energia Recenti / Calcolo Energia", "Energia delle ultime commesse; il calcolo singolo mostra i dettagli di una commessa scelta."],
               ["Report Energetici / Report Giornaliero", "Collegamenti ai report di periodo e alle esportazioni PDF e CSV."],
           ], [5, 12]),
           H2("Impostare una commessa a mano"),
           *elenco("Nella sezione <b>Imposta Commessa</b> inserire il <b>numero di commessa</b> e il <b>codice CER</b> "
                   "(proposto quello di default, 160214). La descrizione è facoltativa.",
                   "Premere il pulsante di invio. Il messaggio verde conferma che il PLC ha ricevuto i dati; "
                   "quello rosso indica che il PLC non è raggiungibile e la commessa <b>non</b> è stata inviata.",
                   "Se la commessa esiste già nel database non ne viene creata un'altra: si aggiorna solo la descrizione."),
           H2("Numerazione automatica"),
           P("Normalmente non serve impostare nulla: a fine lavorazione il sistema prepara da solo la commessa successiva "
             "(ultimo numero + 1, CER di default) e la invia al PLC. Il comportamento si può disattivare dalla "
             "configurazione (sezione 6)."),
           nota("<b>Attenzione.</b> Se il PLC non è raggiungibile a fine lavorazione, la commessa successiva viene comunque "
                "creata nel database in stato “preparazione”, ma il PLC non la riceve. In quel caso impostarla a mano "
                "quando il collegamento torna."),
           ]

    # --- 4
    st += [H1("4. Ciclo di vita di una commessa"),
           P("Il PLC espone due numeri: <b>Commessa RX</b> (quella ricevuta, da lavorare) e <b>Commessa TX</b> "
             "(quella che il PLC conferma in lavorazione o appena chiusa). Il logger riconosce le fasi dalla loro combinazione:"),
           tabella([
               ["RX", "TX", "Fase", "Cosa registra il logger"],
               ["N", "0", "Lavorazione iniziata", "Crea la commessa se manca e salva il contatore dell'energia di partenza. "
                                                  "Se la commessa era già in lavorazione (es. dopo un riavvio) il valore iniziale non viene toccato."],
               ["N", "N", "Registrazione", "Aggiorna ore e minuti della commessa. Dura pochi secondi e può sfuggire alla lettura."],
               ["0", "N", "Lavorazione completata", "Salva il contatore finale e l'energia consumata, salva le ore se mancano, "
                                                    "prepara e invia la commessa N+1."],
               ["0", "0", "Attesa", "Nessuna registrazione."],
           ], [1.2, 1.2, 3.6, 11]),
           Spacer(1, 0.2 * cm),
           tabella([
               ["Stato nel database", "Significato"],
               ["preparazione / non_iniziata", "Commessa creata (automaticamente o a mano), lavorazione non ancora partita."],
               ["in_lavorazione", "Lavorazione partita, energia iniziale salvata."],
               ["completata", "Lavorazione chiusa, energia consumata disponibile."],
           ], [5, 12]),
           ]

    # --- 5
    st += [H1("5. Energia e report"),
           H2("Unità di misura"),
           P("Il PLC fornisce un contatore progressivo dell'energia in centesimi di kWh: un valore di 12345 corrisponde "
             "a 123,45 kWh (fattore <font name='Mono'>RAW_TO_KWH = 100</font> in config.py). Dashboard e report mostrano kWh."),
           nota("Il fattore 100 è dedotto dai dati (circa 5 kW in lavorazione, 0,45 kW a vuoto). Se la potenza nominale "
                "della macchina fosse molto diversa, va verificato con il programmatore del PLC."),
           H2("Ripartizione dell'energia"),
           P("I report dividono l'energia in tre parti:"),
           *elenco("<b>Lavorazione</b>: l'energia della commessa meno la parte di base;",
                   "<b>Base</b>: la macchina accesa ma ferma. Si calcola come 0,41 kW (valore misurato) × (tempo con la "
                   "commessa aperta − tempo di lavorazione), più l'energia consumata tra una commessa e l'altra;",
                   "<b>Non ripartita</b>: commesse per cui il PLC non ha fornito le ore, quindi non divisibili."),
           P("Un salto del contatore di oltre 20 kWh tra due commesse consecutive viene considerato un'interruzione dei "
             "dati (es. cambio di numerazione) e non viene conteggiato."),
           H2("Report disponibili"),
           tabella([
               ["Report", "Pagina web", "Esportazione"],
               ["Giornaliero", "/report/giornaliero?data=AAAA-MM-GG", "/api/export/pdf/giornaliero"],
               ["Mensile", "/report/mensile", "/api/export/pdf/mensile?anno=AAAA&mese=MM"],
               ["Annuale", "/report/annuale", "/api/export/pdf/annuale?anno=AAAA"],
               ["Energia settimanale", "/report/energia/settimanale", "/api/export/pdf/energia/settimanale?inizio=…&fine=…"],
               ["Energia mensile", "/report/energia/mensile", "/api/export/pdf/energia/mensile"],
               ["Energia annuale (con grafico per mese)", "/report/energia/annuale", "/api/export/pdf/energia/annuale"],
               ["Tutti i dati", "—", "/api/export/csv"],
           ], [4.6, 5.8, 6.6]),
           P("Gli indirizzi vanno preceduti da http://192.168.1.9. Dalla dashboard si arriva a tutti con i pulsanti."),
           ]

    # --- 6
    st += [H1("6. Configurazione"),
           P("Ci sono due livelli di configurazione."),
           H2("Configurazione modificabile (dynamic_config.json)"),
           P("Si cambia dalla dashboard o con <font name='Mono'>POST /api/config/update</font>; serve la password "
             "di amministrazione, conservata nel file <font name='Mono'>admin_password.txt</font> sulla Pi."),
           tabella([
               ["Voce", "Valore attuale", "Significato"],
               ["opcua_server_url", "opc.tcp://192.168.1.2:4840", "Indirizzo del server OPC UA del PLC"],
               ["default_cer", "160214", "Codice CER proposto e usato per le commesse automatiche"],
               ["auto_increment_commessa", "sì", "A fine lavorazione prepara la commessa successiva"],
               ["auto_send_to_plc", "sì", "Invia automaticamente al PLC la commessa successiva"],
               ["mode", "opcua", "opcua = collegato al PLC; standalone = solo dashboard, senza PLC"],
           ], [4.4, 4.8, 7.8]),
           H2("Configurazione fissa (config.py)"),
           P("Si cambia modificando il file e riavviando il servizio (sezione 7)."),
           tabella([
               ["Voce", "Valore", "Significato"],
               ["DATABASE_PATH", "telemetria_ricostruita.db", "Database in uso"],
               ["POLLING_INTERVAL", "2 s", "Ogni quanto si legge il PLC"],
               ["RAW_TO_KWH", "100", "Conversione contatore → kWh"],
               ["POTENZA_ATTESA_KW", "0,41", "Potenza a macchina ferma, per la ripartizione"],
               ["WEB_PORT", "80", "Porta della dashboard"],
               ["WEB_DEBUG", "False", "Da attivare solo in sviluppo: mostra i dettagli degli errori nelle pagine"],
           ], [4.4, 4.8, 7.8]),
           ]

    # --- 7
    st += [H1("7. Manutenzione"),
           H2("Accesso alla Raspberry Pi"),
           P("Da remoto attraverso la VPN WireGuard: <font name='Mono'>ssh pi@10.8.0.5</font>. Se il collegamento si "
             "blocca all'avvio, aggiungere <font name='Mono'>-o KexAlgorithms=curve25519-sha256</font> (vedi sezione 9)."),
           H2("Il servizio"),
           codice("""
sudo systemctl status opc_logger      # stato
sudo systemctl restart opc_logger     # riavvio
sudo tail -f /var/log/opc_logger.log  # messaggi in tempo reale
"""),
           P("Il servizio parte da solo all'accensione della Pi. Se il PLC non risponde il servizio resta attivo, "
             "riprova ogni 2 secondi e la dashboard continua a funzionare."),
           H2("Attività automatiche"),
           tabella([
               ["Cosa", "Quando", "Dettagli"],
               ["Backup del database", "ogni giorno (/etc/cron.daily/opc_logger_backup)",
                "Copia coerente con verifica di integrità, compressa in /home/pi/backup_db/. Si tengono 30 giorni."],
               ["Compressione log CSV", "ogni giorno (/etc/cron.daily/opc_logger_csv)",
                "I data_*.log dei giorni passati diventano .log.gz (circa 8 volte più piccoli). I report li leggono comunque."],
               ["Rotazione log del servizio", "ogni giorno (logrotate)",
                "/var/log/opc_logger.log: 7 giorni compressi, massimo 100 MB."],
           ], [4, 5, 8]),
           nota("<b>Da completare.</b> I backup giornalieri restano sulla scheda SD della Pi: se la scheda si guasta si "
                "perdono insieme ai dati. Conviene copiarli periodicamente su un'altra macchina. Una copia di sicurezza "
                "degli archivi storici è sul PC in <font name='Mono'>~/001-Apps/Pileri/raee/archivio_impiantoraee/</font>."),
           H2("Spazio su disco"),
           P("La scheda SD è da 6,7 GB (a novembre 2026 occupata al 48%). Controllare ogni tanto con "
             "<font name='Mono'>df -h /</font>. Nel 2026 il disco si era riempito per il log del servizio non ruotato: "
             "oggi la rotazione lo impedisce."),
           H2("Ripristinare un backup del database"),
           codice("""
sudo systemctl stop opc_logger
cd /home/pi/opc_logger
cp telemetria_ricostruita.db telemetria_ricostruita.db.prima-del-ripristino
gunzip -c /home/pi/backup_db/telemetria_AAAA-MM-GG.db.gz > telemetria_ricostruita.db
sudo systemctl start opc_logger
"""),
           ]

    # --- 8
    st += [H1("8. Aggiornare il software"),
           P("Le modifiche si fanno sul PC, si provano, si salvano nel repository (ramo dev) e poi si portano sulla Pi."),
           *elenco("Prima di sostituire un file sulla Pi farne una copia con la data: "
                   "<font name='Mono'>cp server.py server.py.bak-AAAAMMGG</font>; lo stesso per il database.",
                   "Il tunnel VPN perde i pacchetti grandi, quindi copiare file con scp può bloccarsi. È più sicuro "
                   "far scaricare i file alla Pi direttamente da GitHub:"),
           codice("""
cd /home/pi/opc_logger
git fetch origin dev
git show origin/dev:server.py > /tmp/server.py   # per ogni file modificato
venv/bin/python -m py_compile /tmp/server.py      # controllo prima di installare
cp /tmp/server.py . && sudo systemctl restart opc_logger
"""),
           *elenco("Dopo il riavvio controllare il log del servizio e che la dashboard risponda.",
                   "Non far girare un secondo programma che legge lo stesso PLC o scrive lo stesso database "
                   "(es. il vecchio <font name='Mono'>data_logger.service</font>, oggi disattivato)."),
           ]

    # --- 9
    st += [H1("9. Problemi noti e soluzioni"),
           tabella([
               ["Sintomo", "Causa probabile", "Cosa fare"],
               ["Dashboard ferma, nel log “Connection refused”",
                "Il PLC non accetta la connessione OPC UA. Su 192.168.1.2 rispondono più dispositivi "
                "(rilevata una telecamera Hikvision con lo stesso IP): la Pi a volte parla con quello sbagliato.",
                "Soluzione vera: assegnare un altro IP al dispositivo in conflitto. In alternativa, voce ARP statica sulla Pi "
                "verso il MAC del PLC. Verificare anche che il server OPC UA sia attivo sul PLC (TIA Portal)."],
               ["“Errore nell'invio al PLC” impostando una commessa",
                "PLC non raggiungibile in quel momento.", "Controllare il collegamento al PLC (riga precedente) e riprovare."],
               ["Energia di una commessa troppo bassa o nulla",
                "Interruzioni del collegamento a inizio o fine lavorazione.",
                "I log CSV contengono tutte le letture: gli script correggi_energia_iniziale.py e "
                "ricostruisci_db_da_log.py permettono di ricostruire i valori."],
               ["Ore lavorate a zero",
                "La fase RX=TX dura pochi secondi e non è stata letta.",
                "Dal 10/2026 le ore si salvano anche a fine lavorazione; per lo storico c'è recupera_ore_lavorate.py."],
               ["ssh o scp verso la Pi si bloccano",
                "MTU del tunnel WireGuard: i pacchetti oltre circa 1300 byte si perdono.",
                "ssh con -o KexAlgorithms=curve25519-sha256; impostare MTU = 1280 nella configurazione WireGuard del PC."],
               ["Disco pieno", "Log non ruotati o file temporanei.", "df -h /; controllare /var/log e la cartella del servizio."],
           ], [4, 6, 7]),
           ]

    # --- Appendice
    st += [PageBreak(), H1("Appendice A. Tag OPC UA"),
           P("Namespace 2, prefisso <font name='Mono'>Siemens S7-1200/S7-1500.Tags.</font>"),
           tabella([
               ["Tag", "Direzione", "Contenuto"],
               ["Commessa RX", "scritto dal logger", "Commessa da lavorare"],
               ["Codice CER RX", "scritto dal logger", "Codice CER della commessa da lavorare"],
               ["Commessa TX", "letto", "Commessa in lavorazione o appena chiusa"],
               ["Codice CER TX", "letto", "Codice CER confermato dal PLC"],
               ["Ore / Minuti totali commessa TX", "letto", "Tempo con la commessa aperta"],
               ["Ore / Minuti lavorati commessa TX", "letto", "Tempo effettivo di lavorazione"],
               ["Potenza consumata TX", "letto", "Contatore progressivo dell'energia (centesimi di kWh)"],
           ], [5.5, 3.5, 8]),
           H1("Appendice B. API principali"),
           tabella([
               ["Indirizzo", "Uso"],
               ["GET /api/status", "Stato del servizio di lettura e configurazione in uso"],
               ["GET /api/commesse/recenti?n=5", "Ultime commesse con energia"],
               ["GET /api/commesse/tutte", "Tutte le commesse"],
               ["POST /api/commessa/imposta", "Invia commessa e CER al PLC (JSON: commessa, cer, descrizione)"],
               ["POST /api/commessa/descrizione", "Cambia la descrizione di una commessa"],
               ["GET /api/commessa/energia/&lt;n&gt;", "Energia di una commessa"],
               ["GET /api/energia/statistiche", "Statistiche energetiche"],
               ["GET /api/config, POST /api/config/update", "Legge / modifica la configurazione (con password)"],
               ["POST /api/poller/restart | stop | start", "Riavvia, ferma o avvia il collegamento al PLC"],
           ], [7, 10]),
           H1("Appendice C. File principali"),
           tabella([
               ["File", "Contenuto"],
               ["server.py", "Server web, API e logica delle commesse"],
               ["opcua_reader.py, data_provider.py", "Collegamento al PLC e ciclo di lettura"],
               ["db.py", "Database e report energetici"],
               ["config.py, dynamic_config.json", "Configurazione"],
               ["static/index.html, templates/", "Dashboard e pagine dei report"],
               ["backup_db.sh, comprimi_log_csv.sh", "Copie degli script installati in /etc/cron.daily"],
               ["ricostruisci_db_da_log.py, correggi_energia_iniziale.py, recupera_ore_lavorate.py",
                "Script di recupero dati dai log CSV"],
               ["CLAUDE.md", "Note tecniche e storico degli interventi"],
           ], [7, 10]),
           ]
    return st


if __name__ == "__main__":
    doc = Manuale(USCITA)
    doc.multiBuild(contenuto())
    print(USCITA)
