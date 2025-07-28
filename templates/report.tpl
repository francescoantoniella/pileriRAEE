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

        .navigation {
            margin-bottom: 2rem;
        }

        .summary-card {
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
            <a href="/report/mensile" class="btn btn-outline-info">Report Mensile</a>
            <a href="/report/annuale" class="btn btn-outline-secondary">Report Annuale</a>
        </div>

        <!-- Riepilogo -->
        <div class="summary-card">
            <h3>Riepilogo Giornaliero</h3>
            <div class="row">
                <div class="col-md-3">
                    <strong>Data:</strong> {{titolo.split()[-1]}}
                </div>
                <div class="col-md-3">
                    <strong>Record totali:</strong> {{len(commesse)}}
                </div>
                <div class="col-md-3">
                    <strong>Commesse uniche:</strong> 
                    % if commesse:
                        {{len(set(r['commessa_tx'] for r in commesse if r['commessa_tx']))}}
                    % else:
                        0
                    % end
                </div>
                <div class="col-md-3">
                    <strong>Ore totali lavorate:</strong>
                    % if commesse:
                        {{sum(r['ore_lavorate_commessa_tx'] or 0 for r in commesse)}}
                    % else:
                        0
                    % end
                </div>
            </div>
        </div>

        <!-- Tabella dati -->
        <div class="table-responsive">
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
                        % for riga in commesse: 
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
                    % else:
                        <tr>
                            <td colspan="8" class="text-center text-muted">Nessun dato disponibile per questa data</td>
                        </tr>
                    % end
                </tbody>
            </table>
        </div>

        <!-- Controlli di navigazione -->
        <div class="mt-3">
            <form class="d-inline" method="GET">
                <input type="date" name="data" value="{{titolo.split()[-1]}}" class="form-control d-inline-block" style="width: auto;">
                <button type="submit" class="btn btn-primary">Cambia Data</button>
            </form>
            <a href="/api/export/pdf/giornaliero?data={{titolo.split()[-1]}}" class="btn btn-danger">
                📄 Esporta PDF
            </a>
        </div>
    </div>
</body>
</html> 