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
    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
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
            max-width: 1400px;
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

        .chart-container {
            background-color: #ffffff;
            border-radius: 0.5rem;
            padding: 1.5rem;
            margin-bottom: 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .summary-table {
            background-color: #ffffff;
            border-radius: 0.5rem;
            padding: 1.5rem;
            margin-bottom: 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
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
            <a href="/report/mensile?anno={{anno}}&mese=1" class="btn btn-outline-info">Report Mensili</a>
        </div>

        <!-- Statistiche Annuali -->
        % if statistiche:
        <div class="stats-card">
            <h3>Statistiche Annuali {{anno}}</h3>
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

        <!-- Riepilogo Mensile -->
        <div class="summary-table">
            <h3>Riepilogo Mensile {{anno}}</h3>
            <div class="row">
                % for mese in range(1, 13):
                    <div class="col-md-3 mb-3">
                        <div class="card">
                            <div class="card-body text-center">
                                <h6 class="card-title">
                                    % if mese == 1:
                                        Gennaio
                                    % elif mese == 2:
                                        Febbraio
                                    % elif mese == 3:
                                        Marzo
                                    % elif mese == 4:
                                        Aprile
                                    % elif mese == 5:
                                        Maggio
                                    % elif mese == 6:
                                        Giugno
                                    % elif mese == 7:
                                        Luglio
                                    % elif mese == 8:
                                        Agosto
                                    % elif mese == 9:
                                        Settembre
                                    % elif mese == 10:
                                        Ottobre
                                    % elif mese == 11:
                                        Novembre
                                    % elif mese == 12:
                                        Dicembre
                                    % end
                                </h6>
                                <a href="/report/mensile?anno={{anno}}&mese={{mese}}" class="btn btn-sm btn-outline-primary">
                                    Visualizza
                                </a>
                            </div>
                        </div>
                    </div>
                % end
            </div>
        </div>

        <!-- Grafico Andamento Mensile -->
        <div class="chart-container">
            <h3>Andamento Mensile {{anno}}</h3>
            <canvas id="monthlyChart" width="400" height="200"></canvas>
        </div>

        <!-- Tabella dati (limitata ai primi 50 record) -->
        <div class="table-responsive">
            <h3>Ultimi Record {{anno}}</h3>
            <table class="table table-striped table-bordered">
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Commessa</th>
                        <th>Codice CER</th>
                        <th>Ore totali</th>
                        <th>Minuti totali</th>
                        <th>Ore lavorate</th>
                        <th>Minuti lavorati</th>
                        <th>Energia consumata</th>
                    </tr>
                </thead>
                <tbody>
                    % if commesse:
                        % for riga in commesse[:50]: 
                            <tr>
                                <td>{{riga['timestamp']}}</td>
                                <td>{{riga['commessa_tx']}}</td>
                                <td>{{riga['codice_cer_tx']}}</td>
                                <td>{{riga['ore_totali_commessa_tx']}}</td>
                                <td>{{riga['minuti_totali_commessa_tx']}}</td>
                                <td>{{riga['ore_lavorate_commessa_tx']}}</td>
                                <td>{{riga['minuti_lavorati_commessa_tx']}}</td>
                                <td>{{riga['potenza_consumata_tx']}}</td>
                            </tr>
                        % end
                        % if len(commesse) > 50:
                            <tr>
                                <td colspan="8" class="text-center text-muted">
                                    ... e altri {{len(commesse) - 50}} record
                                </td>
                            </tr>
                        % end
                    % else:
                        <tr>
                            <td colspan="8" class="text-center text-muted">Nessun dato disponibile per questo anno</td>
                        </tr>
                    % end
                </tbody>
            </table>
        </div>

        <!-- Controlli di navigazione -->
        <div class="mt-3">
            <form class="d-inline" method="GET">
                <input type="hidden" name="anno" value="{{anno - 1}}">
                <button type="submit" class="btn btn-outline-secondary">← Anno Precedente</button>
            </form>
            <form class="d-inline" method="GET">
                <input type="hidden" name="anno" value="{{anno + 1}}">
                <button type="submit" class="btn btn-outline-secondary">Anno Successivo →</button>
            </form>
            <a href="/api/export/pdf/annuale?anno={{anno}}" class="btn btn-danger">
                📄 Esporta PDF
            </a>
        </div>
    </div>

    <script>
        // Grafico andamento mensile
        const ctx = document.getElementById('monthlyChart').getContext('2d');
        
        // Dati per il grafico (esempio)
        const monthlyData = {
            labels: ['Gen', 'Feb', 'Mar', 'Apr', 'Mag', 'Giu', 'Lug', 'Ago', 'Set', 'Ott', 'Nov', 'Dic'],
            datasets: [{
                label: 'Record per mese',
                data: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], // Sarà popolato dai dati reali
                backgroundColor: 'rgba(13, 110, 253, 0.2)',
                borderColor: 'rgba(13, 110, 253, 1)',
                borderWidth: 2
            }]
        };

        new Chart(ctx, {
            type: 'bar',
            data: monthlyData,
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    </script>
</body>
</html> 