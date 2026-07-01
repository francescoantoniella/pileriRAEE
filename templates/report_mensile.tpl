<!DOCTYPE html>
<html>
<head>
    <title>{{titolo}}</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Google Font -->
    <link href="https://fonts.googleapis.com/css2?family=Roboto&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Roboto', sans-serif;
            background-color: #f8f9fa;
            padding: 2rem;
        }

        h1 {
            text-align: center;
            margin-bottom: 2rem;
            color: #343a40;
        }

        .table {
            background-color: #ffffff;
            border-radius: 0.5rem;
            overflow: hidden;
        }

        .table th {
            background-color: #0d6efd;
            color: white;
        }

        .table-striped > tbody > tr:nth-of-type(odd) {
            background-color: #f2f2f2;
        }

        .container {
            max-width: 1200px;
            margin: auto;
        }

        .stats-card {
            background-color: #ffffff;
            border-radius: 0.5rem;
            padding: 1.5rem;
            margin-bottom: 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .stat-item {
            text-align: center;
            padding: 1rem;
        }

        .stat-value {
            font-size: 2rem;
            font-weight: bold;
            color: #0d6efd;
        }

        .stat-label {
            color: #6c757d;
            font-size: 0.9rem;
        }

        .navigation {
            margin-bottom: 2rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>{{titolo}}</h1>
        
        <!-- Navigazione -->
        <div class="navigation">
            <a href="/" class="btn btn-outline-primary">← Torna alla Home</a>
            <a href="/report/giornaliero" class="btn btn-outline-secondary">Report Giornaliero</a>
            <a href="/report/annuale?anno={{anno}}" class="btn btn-outline-info">Report Annuale</a>
        </div>

        <!-- Statistiche -->
        % if statistiche:
        <div class="stats-card">
            <h3>Statistiche {{nome_mese}} {{anno}}</h3>
            <div class="row">
                <div class="col-md-2 stat-item">
                    <div class="stat-value">{{statistiche['totale_record']}}</div>
                    <div class="stat-label">Record Totali</div>
                </div>
                <div class="col-md-2 stat-item">
                    <div class="stat-value">{{statistiche['commesse_uniche']}}</div>
                    <div class="stat-label">Commesse Uniche</div>
                </div>
                <div class="col-md-2 stat-item">
                    <div class="stat-value">{{statistiche['ore_totali_lavorate']}}</div>
                    <div class="stat-label">Ore Lavorate</div>
                </div>
                <div class="col-md-2 stat-item">
                    <div class="stat-value">{{statistiche['minuti_totali_lavorati']}}</div>
                    <div class="stat-label">Minuti Lavorati</div>
                </div>
                <div class="col-md-2 stat-item">
                    <div class="stat-value">{{statistiche['energia_totale_consumata']}}</div>
                    <div class="stat-label">Energia Totale (kWh)</div>
                </div>
                <div class="col-md-2 stat-item">
                    <div class="stat-value">{{"%.1f" % statistiche['energia_media_consumata']}}</div>
                    <div class="stat-label">Energia Media (kWh)</div>
                </div>
            </div>
        </div>
        % end

        <!-- Tabella dati -->
        <div class="table-responsive">
            <table class="table table-striped table-bordered">
                <thead>
                    <tr>
                        <th>Ora Chiusura</th>
                        <th>Commessa</th>
                        <th>Codice CER</th>
                        <th>Descrizione</th>
                        <th>Ore totali</th>
                        <th>Minuti totali</th>
                        <th>Ore lavorate</th>
                        <th>Minuti lavorati</th>
                        <th>Energia consumata</th>
                    </tr>
                </thead>
                <tbody>
                    % if commesse:
                        % for riga in commesse: 
                            <tr>
                                <td>{{riga.get('timestamp_formatted', riga['timestamp'])}}</td>
                                <td>{{riga['commessa_tx']}}</td>
                                <td>{{riga['codice_cer_tx']}}</td>
                                <td>{{riga.get('descrizione_commessa', '')}}</td>
                                <td>{{riga['ore_totali_commessa_tx']}}</td>
                                <td>{{riga['minuti_totali_commessa_tx']}}</td>
                                <td>{{riga['ore_lavorate_commessa_tx']}}</td>
                                <td>{{riga['minuti_lavorati_commessa_tx']}}</td>
                                <td>{{"%.3f" % (riga.get('energia_consumata_wh', 0) / 100.0)}} kWh</td>
                            </tr>
                        % end
                    % else:
                        <tr>
                            <td colspan="9" class="text-center text-muted">Nessun dato disponibile per questo periodo</td>
                        </tr>
                    % end
                </tbody>
            </table>
        </div>

        <!-- Controlli di navigazione -->
        <div class="mt-3">
            <form class="d-inline" method="GET">
                <input type="hidden" name="anno" value="{{anno}}">
                <input type="hidden" name="mese" value="{{mese - 1 if mese > 1 else 12}}">
                <button type="submit" class="btn btn-outline-secondary">← Mese Precedente</button>
            </form>
            <form class="d-inline" method="GET">
                <input type="hidden" name="anno" value="{{anno}}">
                <input type="hidden" name="mese" value="{{mese + 1 if mese < 12 else 1}}">
                <button type="submit" class="btn btn-outline-secondary">Mese Successivo →</button>
            </form>
            <a href="/api/export/pdf/mensile?anno={{anno}}&mese={{mese}}" class="btn btn-danger">
                📄 Esporta PDF
            </a>
        </div>
    </div>
</body>
</html> 