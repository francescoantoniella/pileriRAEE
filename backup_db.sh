#!/bin/sh
# Copia giornaliera compressa del DB, tiene gli ultimi 30 giorni.
# Usa l'API di backup di SQLite: copia coerente anche con il servizio in scrittura.
# Installato come /etc/cron.daily/opc_logger_backup.
DEST=/home/pi/backup_db
mkdir -p "$DEST"
F="$DEST/telemetria_$(date +%F).db"
python3 - "$F" <<'EOF' || exit 1
import sqlite3, sys
src = sqlite3.connect('/home/pi/opc_logger/telemetria_ricostruita.db')
dst = sqlite3.connect(sys.argv[1])
src.backup(dst)
esito = dst.execute('PRAGMA integrity_check').fetchone()[0]
dst.close()
if esito != 'ok':
    sys.exit(f"backup {sys.argv[1]}: integrity_check = {esito}")
EOF
gzip -9f "$F"
chown -R pi:pi "$DEST"
find "$DEST" -name 'telemetria_*.db.gz' -mtime +30 -delete
exit 0
