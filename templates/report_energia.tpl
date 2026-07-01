<!DOCTYPE html>
<html>
<head>
    <title>{{titolo}}</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <style>
        body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Helvetica, Arial, "Apple Color Emoji", "Segoe UI Emoji"; background:#f8f9fa; padding:2rem; }
        .container { max-width: 1100px; margin:auto; }
        .card { box-shadow: 0 2px 4px rgba(0,0,0,0.06); }
        .stat-value { font-size: 1.6rem; font-weight: 700; color:#0d6efd; }
        .stat-label { color:#6c757d; font-size: .9rem; }
    </style>
    % import json
</head>
<body>
<div class="container">
    <h1 class="mb-4">{{titolo}}</h1>

    <div class="mb-3 d-flex gap-2 align-items-center">
        <a href="/" class="btn btn-outline-primary">← Home</a>
        <a href="/report/energia/settimanale" class="btn btn-outline-secondary">Settimanale</a>
        <a href="/report/energia/mensile" class="btn btn-outline-secondary">Mensile</a>
        <a href="/report/energia/annuale" class="btn btn-outline-secondary">Annuale</a>
        % if livello == 'mensile':
        <a class="btn btn-danger ms-auto" href="/api/export/pdf/energia/mensile?anno={{anno}}&mese={{mese}}">📄 Scarica PDF</a>
        % elif livello == 'annuale':
        <a class="btn btn-danger ms-auto" href="/api/export/pdf/energia/annuale?anno={{anno}}">📄 Scarica PDF</a>
        % elif livello == 'settimanale':
        <a class="btn btn-danger ms-auto" href="/api/export/pdf/energia/settimanale?inizio={{inizio}}&fine={{fine}}">📄 Scarica PDF</a>
        % end
    </div>

    <div class="row g-3 mb-4">
        <div class="col-md-4">
            <div class="card p-3">
                <div class="stat-value">{{"%.3f" % report['energia_totale_kwh']}} kWh</div>
                <div class="stat-label">Energia totale</div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card p-3">
                <div class="stat-value">{{"%.3f" % report['energia_lavorazioni_kwh']}} kWh</div>
                <div class="stat-label">Energia lavorazioni</div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card p-3">
                <div class="stat-value">{{"%.3f" % report['energia_standby_kwh']}} kWh</div>
                <div class="stat-label">Energia standby</div>
            </div>
        </div>
    </div>

    <div class="row g-4 mb-4">
        <div class="col-md-6">
            <div class="card p-3">
                <h5>Ripartizione energia</h5>
                <canvas id="pieChart"></canvas>
            </div>
        </div>
        <div class="col-md-6">
            <div class="card p-3">
                <h5>Commesse completate</h5>
                <div class="display-6">{{report['commesse_completate']}}</div>
                <div class="text-muted">Nel periodo selezionato</div>
                <div class="mt-3 small text-muted">Prima lettura: {{report['prima_lettura_wh']}} Wh · Ultima: {{report['ultima_lettura_wh']}} Wh · Letture: {{report['totale_letture']}}</div>
            </div>
        </div>
    </div>

    <div class="card p-3 mb-4">
        <h5>Dettaglio commesse completate</h5>
        <div class="table-responsive">
            <table class="table table-striped table-bordered">
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Commessa</th>
                        <th>Energia (Wh)</th>
                        <th>Energia (kWh)</th>
                        <th>Descrizione</th>
                    </tr>
                </thead>
                <tbody>
                % if report['commesse_dettaglio']:
                    % for c in report['commesse_dettaglio']:
                        <tr>
                            <td>{{c['timestamp']}}</td>
                            <td>{{c['commessa_tx']}}</td>
                            <td>{{c['energia_consumata_wh']}}</td>
                            <td>{{"%.3f" % (c['energia_consumata_wh']/100.0)}}</td>
                            <td>{{c.get('descrizione_commessa','')}}</td>
                        </tr>
                    % end
                % else:
                    <tr><td colspan="5" class="text-muted text-center">Nessuna commessa completata</td></tr>
                % end
                </tbody>
            </table>
        </div>
    </div>

    <script>
        const pieCtx = document.getElementById('pieChart');
        const dati = {
            labels: ['Lavorazioni', 'Standby'],
            datasets: [{
                data: [{{report['energia_lavorazioni_kwh']}}, {{report['energia_standby_kwh']}}],
                backgroundColor: ['#0d6efd','#6c757d']
            }]
        };
        new Chart(pieCtx, { type: 'pie', data: dati, options: { plugins: { legend: { position: 'bottom' } } } });
    </script>
</div>
</body>
</html>

