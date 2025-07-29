
<!DOCTYPE html>
<html>
<head>
    <title>OPC Logger - Dashboard</title>
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
            max-width: 1400px;
            margin: auto;
        }

        .status-card {
            background-color: #ffffff;
            border-radius: 0.5rem;
            padding: 1.5rem;
            margin-bottom: 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }

        .status-online {
            background-color: #28a745;
        }

        .status-offline {
            background-color: #dc3545;
        }

        .status-warning {
            background-color: #ffc107;
        }

        .collapsible {
            cursor: pointer;
        }

        .collapsible:hover {
            background-color: #f8f9fa;
        }

        .collapsible-content {
            display: none;
            padding: 1rem;
            border-top: 1px solid #dee2e6;
        }

        .commessa-form {
            background-color: #e3f2fd;
            border: 2px solid #2196f3;
            border-radius: 0.5rem;
            padding: 1.5rem;
            margin-bottom: 2rem;
        }

        .report-section {
            background-color: #f3e5f5;
            border: 2px solid #9c27b0;
            border-radius: 0.5rem;
            padding: 1.5rem;
            margin-bottom: 2rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Impianto trattamento RAEE - Dashboard</h1>
        
        <!-- Sezione Commessa - Sempre visibile -->
        <div class="commessa-form">
            <h3>🎯 Gestione Commessa</h3>
            <form id="commessaForm" class="row g-3">
                <div class="col-md-4">
                    <label for="commessa" class="form-label">Numero Commessa</label>
                    <input type="number" class="form-control" id="commessa" name="commessa" required>
                </div>
                <div class="col-md-4">
                    <label for="cer" class="form-label">Codice CER</label>
                    <select class="form-select" id="cer" name="cer" required>
                        <option value="">Seleziona CER</option>
                        <option value="160214">160214</option>
                        <option value="200000">200000</option>
                    </select>
                </div>
                <div class="col-md-4">
                    <label class="form-label">&nbsp;</label>
                    <div>
                        <button type="submit" class="btn btn-primary">Imposta Commessa</button>
                        <button type="button" class="btn btn-success" onclick="incrementaCommessa()">+1</button>
                    </div>
                </div>
            </form>
            <div id="commessaStatus" class="mt-2"></div>
        </div>

        <!-- Sezione Report - Espansa di default -->
        <div class="report-section">
            <h3>📊 Report e Analisi</h3>
            <div class="row">
                <div class="col-md-3">
                    <a href="/report/giornaliero" class="btn btn-outline-primary w-100 mb-2">📅 Report Giornaliero</a>
                </div>
                <div class="col-md-3">
                    <a href="/report/mensile" class="btn btn-outline-info w-100 mb-2">📈 Report Mensile</a>
                </div>
                <div class="col-md-3">
                    <a href="/report/annuale" class="btn btn-outline-secondary w-100 mb-2">📊 Report Annuale</a>
                </div>
                <div class="col-md-3">
                    <a href="/api/commesse/tutte" class="btn btn-outline-dark w-100 mb-2">📋 Tutti i Dati</a>
                </div>
            </div>
        </div>

        <!-- Sezione Dati Recenti - Espansa di default -->
        <div class="status-card">
            <h3>📋 Dati Recenti</h3>
            <div class="row align-items-center mb-3">
                <div class="col-md-6">
                    <p class="mb-0">Mostrando <strong>{{num_records}}</strong> record più recenti</p>
                </div>
                <div class="col-md-6">
                    <form method="GET" class="d-flex">
                        <input type="number" name="n" value="{{num_records}}" min="1" max="100" class="form-control me-2" style="width: auto;">
                        <button type="submit" class="btn btn-primary">Cambia</button>
                    </form>
                </div>
            </div>
            <div class="mb-3">
                <small class="text-muted">Suggerimenti: </small>
                <a href="/?n=10" class="btn btn-sm btn-outline-secondary">10</a>
                <a href="/?n=25" class="btn btn-sm btn-outline-secondary">25</a>
                <a href="/?n=50" class="btn btn-sm btn-outline-secondary">50</a>
                <a href="/?n=100" class="btn btn-sm btn-outline-secondary">100</a>
            </div>

            <div class="table-responsive">
                <table class="table table-striped table-bordered">
                    <thead>
                        <tr>
                            <th>Ora Chiusura</th>
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
                                    <td>{{riga.get('timestamp_formatted', riga['timestamp'])}}</td>
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
                                <td colspan="8" class="text-center text-muted">Nessun dato disponibile</td>
                            </tr>
                        % end
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Sezione Sistema - Collassabile -->
        <div class="status-card">
            <h4 class="collapsible" onclick="toggleSection('systemSection')">
                ⚙️ Stato del Sistema <span id="systemArrow">▼</span>
            </h4>
            <div id="systemSection" class="collapsible-content">
                <div id="system-status">
                    <p><span class="status-indicator status-warning"></span>Caricamento stato...</p>
                </div>
                <div class="mt-3">
                    <button class="btn btn-primary btn-sm" onclick="restartPoller()">Riavvia Poller</button>
                    <button class="btn btn-success btn-sm" onclick="startPoller()">Avvia Poller</button>
                    <button class="btn btn-warning btn-sm" onclick="stopPoller()">Ferma Poller</button>
                    <a href="/api/export/csv" class="btn btn-info btn-sm">Esporta CSV</a>
                </div>
            </div>
        </div>

        <!-- Pannello Configurazione - Collassabile -->
        <div class="status-card">
            <h4 class="collapsible" onclick="toggleSection('configSection')">
                🔧 Configurazione Sistema <span id="configArrow">▶</span> <span class="badge bg-warning">Admin</span>
            </h4>
            <div id="configSection" class="collapsible-content">
                <div class="alert alert-warning">
                    <strong>⚠️ Attenzione:</strong> Questa sezione è riservata agli amministratori.
                </div>
                
                <div class="row">
                    <div class="col-md-6">
                        <h5>🔗 Configurazione OPC UA</h5>
                        <form id="config-form">
                            <div class="mb-3">
                                <label for="opcua-url" class="form-label">URL Server OPC UA:</label>
                                <input type="text" class="form-control" id="opcua-url" placeholder="opc.tcp://192.168.1.2:4840">
                            </div>
                            <div class="mb-3">
                                <label for="opcua-namespace" class="form-label">Namespace Index:</label>
                                <input type="number" class="form-control" id="opcua-namespace" value="2">
                            </div>
                            <div class="mb-3">
                                <label for="opcua-prefix" class="form-label">Tag Prefix:</label>
                                <input type="text" class="form-control" id="opcua-prefix" placeholder="Siemens S7-1200/S7-1500.Tags.">
                            </div>
                        </form>
                    </div>
                    
                    <div class="col-md-6">
                        <h5>🎯 Configurazione Comportamento</h5>
                        <form id="behavior-form">
                            <div class="mb-3">
                                <label for="default-cer" class="form-label">CER di Default:</label>
                                <input type="number" class="form-control" id="default-cer" value="160214">
                            </div>
                            <div class="mb-3">
                                <div class="form-check">
                                    <input class="form-check-input" type="checkbox" id="auto-increment" checked>
                                    <label class="form-check-label" for="auto-increment">
                                        Auto-increment Commessa
                                    </label>
                                </div>
                            </div>
                            <div class="mb-3">
                                <div class="form-check">
                                    <input class="form-check-input" type="checkbox" id="auto-send" checked>
                                    <label class="form-check-label" for="auto-send">
                                        Invio Automatico al PLC
                                    </label>
                                </div>
                            </div>
                            <div class="mb-3">
                                <label for="system-mode" class="form-label">Modalità Sistema:</label>
                                <select class="form-control" id="system-mode">
                                    <option value="opcua">OPC UA</option>
                                    <option value="standalone">Standalone</option>
                                </select>
                            </div>
                        </form>
                    </div>
                </div>
                
                <div class="row mt-3">
                    <div class="col-12">
                        <!-- Password nascosta per sicurezza -->
                        <div class="mb-3">
                            <label for="admin-password" class="form-label">Password:</label>
                            <input type="password" class="form-control" id="admin-password" placeholder="Inserisci password">
                        </div>
                        <button class="btn btn-primary" onclick="saveConfig()">💾 Salva Configurazione</button>
                        <button class="btn btn-secondary" onclick="resetConfig()">🔄 Reset Configurazione</button>
                        <button class="btn btn-warning" onclick="restartPoller()">🔄 Riavvia Poller</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Funzione per incrementare la commessa
        function incrementaCommessa() {
            const commessaInput = document.getElementById('commessa');
            const currentValue = parseInt(commessaInput.value) || 0;
            commessaInput.value = currentValue + 1;
        }

        // Funzione per gestire il form della commessa
        document.getElementById('commessaForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const commessa = document.getElementById('commessa').value;
            const cer = document.getElementById('cer').value;
            
            if (!commessa || !cer) {
                alert('Inserisci sia la commessa che il codice CER');
                return;
            }

            fetch('/api/commessa/imposta', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    commessa: parseInt(commessa),
                    cer: parseInt(cer)
                })
            })
            .then(response => response.json())
            .then(data => {
                const statusDiv = document.getElementById('commessaStatus');
                if (data.success) {
                    statusDiv.innerHTML = '<div class="alert alert-success">Commessa impostata con successo!</div>';
                    // Incrementa automaticamente la commessa per la prossima volta
                    document.getElementById('commessa').value = parseInt(commessa) + 1;
                } else {
                    statusDiv.innerHTML = '<div class="alert alert-danger">Errore: ' + (data.error || 'Errore sconosciuto') + '</div>';
                }
            })
            .catch(error => {
                document.getElementById('commessaStatus').innerHTML = '<div class="alert alert-danger">Errore di connessione</div>';
            });
        });

        // Funzione per collassare/espandere sezioni
        function toggleSection(sectionId) {
            const content = document.getElementById(sectionId);
            const arrow = document.getElementById(sectionId.replace('Section', 'Arrow'));
            
            if (content.style.display === 'none') {
                content.style.display = 'block';
                arrow.textContent = '▼';
            } else {
                content.style.display = 'none';
                arrow.textContent = '▶';
            }
        }

        // Funzione per aggiornare lo stato del sistema
        function updateStatus() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    const statusDiv = document.getElementById('system-status');
                    let statusHtml = '';
                    
                    // Aggiorna anche la configurazione se disponibile
                    if (data.config) {
                        document.getElementById('opcua-url').value = data.config.opcua_server_url || '';
                        document.getElementById('default-cer').value = data.config.default_cer || 160214;
                        document.getElementById('auto-increment').checked = data.config.auto_increment_commessa || false;
                        document.getElementById('auto-send').checked = data.config.auto_send_to_plc || false;
                        document.getElementById('system-mode').value = data.mode || 'opcua';
                        
                        // Aggiorna anche il CER nella dropdown principale
                        const cerSelect = document.getElementById('cer');
                        if (cerSelect && data.config.default_cer) {
                            cerSelect.value = data.config.default_cer.toString();
                        }
                    }
                    
                    // Stato del poller
                    const pollerStatus = data.poller_running ? 'status-online' : 'status-offline';
                    const pollerText = data.poller_running ? 'Online' : 'Offline';
                    statusHtml += `<p><span class="status-indicator ${pollerStatus}"></span>Poller: ${pollerText}</p>`;
                    
                    // Modalità
                    statusHtml += `<p><span class="status-indicator status-warning"></span>Modalità: ${data.mode}</p>`;
                    
                    // Database
                    const dbStatus = data.database_available ? 'status-online' : 'status-offline';
                    const dbText = data.database_available ? 'Disponibile' : 'Non disponibile';
                    statusHtml += `<p><span class="status-indicator ${dbStatus}"></span>Database: ${dbText}</p>`;
                    
                    statusDiv.innerHTML = statusHtml;
                })
                .catch(error => {
                    console.error('Errore nel caricamento dello stato:', error);
                    document.getElementById('system-status').innerHTML = 
                        '<p><span class="status-indicator status-offline"></span>Errore nel caricamento dello stato</p>';
                });
        }

        // Funzioni per controllare il poller
        function restartPoller() {
            fetch('/api/poller/restart', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    alert(data.message);
                    setTimeout(updateStatus, 1000);
                })
                .catch(error => {
                    alert('Errore nel riavvio del poller');
                });
        }

        function startPoller() {
            fetch('/api/poller/start', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    alert(data.message);
                    setTimeout(updateStatus, 1000);
                })
                .catch(error => {
                    alert('Errore nell\'avvio del poller');
                });
        }

        function stopPoller() {
            fetch('/api/poller/stop', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    alert(data.message);
                    setTimeout(updateStatus, 1000);
                })
                .catch(error => {
                    alert('Errore nella fermata del poller');
                });
        }

        // Funzione per salvare la configurazione
        function saveConfig() {
            const password = document.getElementById('admin-password').value;
            if (!password) {
                alert('Inserisci la password amministratore');
                return;
            }
            
            const config = {
                password: password,
                opcua_server_url: document.getElementById('opcua-url').value,
                opcua_namespace_index: parseInt(document.getElementById('opcua-namespace').value),
                opcua_tag_prefix: document.getElementById('opcua-prefix').value,
                default_cer: parseInt(document.getElementById('default-cer').value),
                auto_increment_commessa: document.getElementById('auto-increment').checked,
                auto_send_to_plc: document.getElementById('auto-send').checked,
                mode: document.getElementById('system-mode').value
            };
            
            fetch('/api/config/update', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(config)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('✅ Configurazione salvata con successo!');
                    document.getElementById('admin-password').value = '';
                    // Aggiorna il CER di default nella dropdown principale
                    setDefaultCer();
                } else {
                    alert('❌ Errore: ' + (data.error || 'Errore sconosciuto'));
                }
            })
            .catch(error => {
                alert('❌ Errore di connessione');
            });
        }

        // Funzione per resettare la configurazione
        function resetConfig() {
            const password = document.getElementById('admin-password').value;
            if (!password) {
                alert('Inserisci la password amministratore');
                return;
            }
            
            if (!confirm('Sei sicuro di voler resettare la configurazione ai valori di default?')) {
                return;
            }
            
            fetch('/api/config/reset', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ password: password })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('✅ Configurazione resettata con successo!');
                    document.getElementById('admin-password').value = '';
                    updateStatus(); // Ricarica la configurazione
                } else {
                    alert('❌ Errore: ' + (data.error || 'Errore sconosciuto'));
                }
            })
            .catch(error => {
                alert('❌ Errore di connessione');
            });
        }

        // Inizializzazione
        updateStatus();
        setInterval(updateStatus, 30000);
        
        // Carica l'ultima commessa e incrementala
        fetch('/api/commessa/ultima')
            .then(response => response.json())
            .then(data => {
                if (data.ultima_commessa && data.ultima_commessa > 0) {
                    document.getElementById('commessa').value = data.ultima_commessa + 1;
                }
            })
            .catch(error => {
                console.error('Errore nel caricamento dell\'ultima commessa:', error);
            });

        // Imposta il CER di default dalla configurazione
        function setDefaultCer() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    if (data.config && data.config.default_cer) {
                        const cerSelect = document.getElementById('cer');
                        cerSelect.value = data.config.default_cer.toString();
                    }
                })
                .catch(error => {
                    console.error('Errore nel caricamento del CER di default:', error);
                });
        }

        // Imposta il CER di default al caricamento della pagina
        setDefaultCer();
    </script>
</body>
</html>
